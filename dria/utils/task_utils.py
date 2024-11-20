import copy
import copy
import json
import random
import re
import secrets
import string
import time
from typing import List, Any, Dict, Union

from dria_workflows import Workflow
from fastbloom_rs import BloomFilter
from json_repair import repair_json

from dria.constants import INPUT_CONTENT_TOPIC, TASK_DEADLINE
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import NodeModel, Task, TaskModel, TaskInputModel
from dria.models.enums import (
    Model,
    OpenAIModels,
    OllamaModels,
    CoderModels,
    GeminiModels,
)
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utils import str_to_base64
from dria.utils.logging import logger
from dria.utils.node_selection import select_nodes
from dria.utils.schema_parser import SchemaParser


class TaskManager:
    """
    Manages task lifecycle including creation, publishing, and node selection.

    Handles:
    - Task preparation and publishing to network
    - Node selection and filtering
    - Task state management
    - Node availability tracking
    """

    def __init__(self, storage: Storage, rpc: RPCClient, kv: KeyValueQueue):
        """
        Initialize TaskManager.

        Args:
            storage: Storage backend for persisting task/node data
            rpc: RPC client for network communication
            kv: Key-value queue for task messaging
        """
        self.storage = storage
        self.rpc = rpc
        self.kv = kv

    @staticmethod
    def _schema_parser(workflow: Workflow, selected_model: str) -> Dict:
        """Parse schema for task model."""
        for t in workflow.tasks:
            if t.schema is None:
                continue
            provider = None
            if selected_model in [m.value for m in OpenAIModels]:
                provider = Model.OPENAI.value
            elif selected_model in [m.value for m in OllamaModels]:
                provider = Model.OLLAMA.value
            elif selected_model in [m.value for m in CoderModels]:
                continue
            elif selected_model in [m.value for m in GeminiModels]:
                provider = Model.GEMINI.value
            schema = SchemaParser.parse(t.schema, provider)
            t.schema = schema

        return workflow.model_dump(warnings=False)

    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Generate a cryptographically secure random string.

        Args:
            length: Length of string to generate, defaults to 32

        Returns:
            Random string of specified length
        """
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )

    async def publish_message(self, task: str, content_topic: str) -> bool:
        """
        Publish a task message to specified content topic.

        Args:
            task: Task data to publish
            content_topic: Topic to publish to

        Returns:
            True if published successfully

        Raises:
            TaskPublishError: If publishing fails
        """
        try:
            return await self.rpc.push_content_topic(
                data=str_to_base64(task), content_topic=content_topic
            )
        except Exception as e:
            raise TaskPublishError(f"Failed to publish task: {e}") from e

    async def prepare_task(self, task: Task) -> Task:
        """
        Prepare task for publishing by generating ID, deadline and selecting nodes.

        Args:
            task: Task to prepare
            node_stats: Dict of stats nodes

        Returns:
            Tuple of task model dict and prepared task

        Raises:
            TaskFilterError: If node selection fails
        """
        task.id = self.generate_random_string()
        deadline = int(time.time_ns() + TASK_DEADLINE * 1e9)

        task.deadline = deadline
        task.created_ts = int(time.time_ns())

        return task

    async def save_workflow(self, task: Task):
        await self.storage.set_value(
            f"{task.id}:workflow", copy.deepcopy(task.workflow)
        )

    async def push_task(self, task: Task):
        """
        Push prepared task to network.

        Args:
            task: Task to push

        Returns:
            Tuple of (success bool, list of selected nodes if successful)
        """
        is_retried = False
        if task.id is not None:
            is_retried = True
            old_task_id = task.__deepcopy__().id

        task = await self.prepare_task(task)
        await self.save_workflow(task)
        if isinstance(task.workflow, Workflow):
            parsed_workflow = self._schema_parser(task.workflow, task.models[0])
            task.workflow = parsed_workflow
        task_model = TaskModel(
            taskId=task.id,
            filter=task.filter,
            input=TaskInputModel(workflow=task.workflow, model=task.models).dict(),
            pickedNodes=task.nodes,
            deadline=task.deadline,
            publicKey=task.public_key[2:],
            privateKey=task.private_key,
        ).dict()
        task_model_str = json.dumps(task_model, ensure_ascii=False)

        if await self.publish_message(task_model_str, INPUT_CONTENT_TOPIC):
            await self.storage.set_value(
                f"{task.id}", json.dumps(task.dict(), ensure_ascii=False)
            )
            if is_retried:
                await self.kv.push(f":{old_task_id}", {"new_task_id": task.id})

    async def get_available_nodes(self, model_type: str) -> List[str]:
        """
        Get list of available nodes for specified model type.

        Args:
            model_type: Type of model to get nodes for

        Returns:
            List of available node addresses
        """
        try:
            available_nodes = await self.storage.get_value(
                f"available-nodes-{model_type}"
            )
            return json.loads(available_nodes) if available_nodes else []
        except Exception as e:
            logger.error(f"Error getting available nodes for {model_type}: {e}")
            return []

    async def create_filter(
        self,
        tasks: List[Task],
        node_stats: Dict[str, int],
    ) -> (
        tuple[None, None, None]
        | tuple[list[str], list[dict[str, int | str]], list[list[Any]]]
    ):
        """
        Create Bloom filter for node selection.

        Args:
            node_stats: Dict of nodes stats
            retry: Number of retries attempted

        Returns:
            Tuple of (selected nodes, selected model, Bloom filter params)
        """

        models = list(set([x for i in tasks for x in i.models]))
        # Get all available nodes for all models
        all_model_nodes = {}
        for model in models:
            nodes = await self.get_available_nodes(model)
            if nodes:
                all_model_nodes[model] = nodes

        if not all_model_nodes:
            return None, None, None
        stats_for_model_nodes = {}
        seen_nodes = set()
        for model, nodes in all_model_nodes.items():
            for node in nodes:
                # Skip if we've already processed this node
                if node in seen_nodes:
                    continue
                seen_nodes.add(node)

                # Find matching stat for this node
                matching_stat = next(
                    ({n: s} for n, s in node_stats.items() if n == node), None
                )
                if matching_stat:
                    stats_for_model_nodes.update(matching_stat)
                else:
                    # If no matching stat found, add default score of 0.5
                    stats_for_model_nodes[node] = 0.5

        # Count frequency of each node in samples
        node_frequencies = {}
        for node in select_nodes(stats_for_model_nodes, len(tasks)):
            node_frequencies[node] = node_frequencies.get(node, 0) + 1

        # Calculate final score as base score * frequency
        weighted_scores = {}
        for node, freq in node_frequencies.items():
            weighted_scores[node] = stats_for_model_nodes[node] * freq

        # Sort by weighted score and take top nodes
        picked_nodes = sorted(
            weighted_scores.items(), key=lambda x: x[1], reverse=True
        )[: len(tasks)]
        picked_nodes = [node for node, _ in picked_nodes]
        sampled_stat = {}
        for node in picked_nodes:
            sampled_stat[node] = stats_for_model_nodes[node]

        picked_nodes = select_nodes(sampled_stat, len(tasks))

        for model in models:
            try:
                await self.storage.remove_from_list(
                    f"available-nodes-{model}", None, picked_nodes
                )
            except ValueError:
                logger.debug(
                    f"Node {picked_nodes} not found in available nodes for model {model}"
                )

        filters = []
        node_models = []

        for node in picked_nodes:
            bf = BloomFilter(len(node) * 2 + 1, 0.001)
            bf.add(bytes.fromhex(node))
            filters.append({"hex": bf.get_bytes().hex(), "hashes": bf.hashes()})

            supported_models = []
            for model, model_nodes in all_model_nodes.items():
                if node in model_nodes:
                    supported_models.append(model)
            random_model = random.choice(supported_models)
            node_models.append([random_model])

        logger.debug(f"Selected nodes: {picked_nodes}")
        return (picked_nodes, filters, node_models)

    async def add_available_nodes(self, node_model: NodeModel, model_type: str) -> bool:
        """
        Add nodes to available pool for specified model type.

        Args:
            node_model: Node model containing nodes to add
            model_type: Type of model nodes support

        Returns:
            True if nodes added successfully
        """
        try:
            await self.storage.set_value(
                f"available-nodes-{model_type}",
                json.dumps(node_model.nodes, ensure_ascii=False),
            )
            return True
        except Exception as e:
            logger.error(f"Error adding available nodes: {e}")
            return False


def parse_json(text: Union[str, List]) -> Union[List[Dict], Dict]:
    """
    Parse JSON from text, handling various formats.

    Supports:
    - Raw JSON
    - JSON in code blocks
    - JSON in <JSON> tags
    - Lists of JSON strings

    Args:
        text: Text containing JSON to parse

    Returns:
        Parsed JSON as dict or list of dicts

    Raises:
        ValueError: If JSON parsing fails
    """

    def parse_single_json(result: str) -> Dict:
        patterns = [
            r"```(?:JSON)?\s*(.*?)\s*```",
            r"<JSON>\s*(.*?)\s*</JSON>",
        ]

        for pattern in patterns:
            match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
            if match:
                json_text = match.group(1)
                break
        else:
            json_text = result

        try:
            return repair_json(json_text, return_objects=True)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {json_text}") from e

    if isinstance(text, list):
        return [parse_single_json(item) for item in text]
    return parse_single_json(text)


def extract_backtick_label(text, label):
    """
    Extracts content between backticks with specified label

    Args:
        text (str): Input text containing backtick blocks
        label (str): Label to match (e.g., 'python', 'csv')

    Returns:
        list: List of content found between matching backtick blocks
    """
    import re

    # Create pattern for matching backticks with label
    pattern = f"```{label}(.*?)```"

    # Find all matches using regex
    # re.DOTALL flag allows . to match newlines
    matches = re.findall(pattern, text, re.DOTALL)

    # Strip whitespace from matches
    return [match.strip() for match in matches]
