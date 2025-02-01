import copy
import hashlib
import json
import random
import re
import secrets
import string
import time
from typing import List, Any, Dict, Union, Tuple
import traceback

from dria_workflows import Workflow
from fastbloom_rs import BloomFilter
from json_repair import repair_json

from dria.constants import INPUT_CONTENT_TOPIC, TASK_DEADLINE, COMPUTE_NODE_BATCH_SIZE
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import NodeModel, Task, TaskModel, TaskInputModel
from dria.models.enums import (
    Model,
    OpenAIModels,
    OllamaModels,
    CoderModels,
    GeminiModels,
    OpenRouterModels,
    ReasoningModels,
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
            storage: Storage backend for persisting task/node data.
            rpc: RPC client for network communication.
            kv: Key-value queue for task messaging.
        """
        self.storage = storage
        self.rpc = rpc
        self.kv = kv

    @staticmethod
    def _schema_parser(workflow: Workflow, selected_model: str) -> Dict[str, Any]:
        """
        Parse schema for the given workflow and selected model.

        Args:
            workflow (Workflow): The workflow instance containing multiple tasks.
            selected_model (str): The model selected (e.g., "openai-gpt", "ollama").

        Returns:
            Dict[str, Any]: A dictionary representation of the workflow with parsed schema.
        """
        # Iterate through the tasks in the workflow
        for t in workflow.tasks:
            if t.schema is None:
                continue

            # Determine which provider to use for schema parsing
            provider = None
            if selected_model in [m.value for m in OpenAIModels]:
                provider = Model.OPENAI.value
            elif selected_model in [m.value for m in OllamaModels]:
                provider = Model.OLLAMA.value
            elif selected_model in [m.value for m in CoderModels]:
                # Coder models might not require schema parsing
                continue
            elif selected_model in [m.value for m in ReasoningModels]:
                continue
            elif selected_model in [m.value for m in GeminiModels]:
                provider = Model.GEMINI.value
            elif selected_model in [m.value for m in OpenRouterModels]:
                provider = Model.OPENROUTER.value

            # Parse and replace the schema
            if provider:
                schema = SchemaParser.parse(t.schema, provider)
                t.schema = schema

        # Return the fully updated workflow as a dictionary
        return workflow.model_dump(warnings=False)

    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Generate a cryptographically secure random string.

        Args:
            length (int): Length of the string to generate; defaults to 32.

        Returns:
            str: Random string of specified length.
        """
        # Using secrets.choice for better security
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )

    async def publish_message(self, task: str, content_topic: str) -> bool:
        """
        Publish a task message to the specified content topic.

        Args:
            task (str): Task data (as a JSON-serialized string) to publish.
            content_topic (str): Topic to publish the task to.

        Returns:
            bool: True if published successfully, otherwise raises an exception.

        Raises:
            TaskPublishError: If publishing fails.
        """
        try:
            # Convert the task data to base64 and push it to the designated content topic
            return await self.rpc.push_content_topic(
                data=str_to_base64(task), content_topic=content_topic
            )
        except Exception as e:
            raise TaskPublishError(f"Failed to publish task: {e}") from e

    async def prepare_task(self, task: Task) -> Task:
        """
        Prepare task for publishing by generating ID, deadline, timestamps, etc.

        Args:
            task (Task): The Task instance to prepare.

        Returns:
            Task: The same task instance with ID and metadata fields updated.
        """
        # Generate unique ID for this task
        task.id = self.generate_random_string()

        # Calculate deadline (in nanoseconds)
        deadline_ns = int(time.time_ns() + TASK_DEADLINE * 1e9)
        task.deadline = deadline_ns

        # Store creation timestamp (in nanoseconds)
        task.created_ts = int(time.time_ns())

        return task

    async def save_workflow(self, task: Task) -> None:
        """
        Save the workflow to storage.

        Args:
            task (Task): The Task containing the workflow to be saved.
        """
        # Store a copy of the workflow in the storage under key "<task.id>:workflow"
        await self.storage.set_value(
            f"{task.id}:workflow", copy.deepcopy(task.workflow)
        )

    async def push_task(self, task: Task, selected_model: List[str]) -> None:
        """
        Push the prepared task to the network, optionally retrying if an old ID is present.

        Args:
            task (Task): The Task instance to push.
            selected_model (List[str]): List of model(s) to use for the task.
        """
        # Check if this is a retry
        is_retried = False
        old_task_id = None
        if task.id is not None:
            is_retried = True
            old_task_id = task.__deepcopy__().id

        # Prepare task by assigning new ID, deadline, etc.
        task = await self.prepare_task(task)

        # Save the workflow in storage
        await self.save_workflow(task)

        # If the workflow is a Workflow object, parse the schema for the first selected model
        if isinstance(task.workflow, Workflow):
            parsed_workflow = self._schema_parser(task.workflow, selected_model[0])
            task.workflow = parsed_workflow

        peer_ids = [
            await self.storage.get_value(f"{node}:peer_id") or None
            for node in task.nodes
        ]
        if None in peer_ids:
            raise ValueError(
                "PeerID not found for some nodes"
            ) from traceback.extract_stack()

        # Create TaskModel data structure
        task_model = TaskModel(
            taskId=task.id,
            filter=task.filter,
            input=TaskInputModel(
                workflow=task.workflow, model=selected_model
            ).model_dump(),
            pickedNodes=task.nodes,
            nodePeerIds=peer_ids,
            deadline=task.deadline,
            datasetId=hashlib.sha256(
                (self.rpc.headers.get("x-api-key") + task.dataset_id).encode()
            ).hexdigest(),
            publicKey=task.public_key[2:],  # Typically removing '0x' prefix if present
            privateKey=task.private_key,
        ).model_dump()

        # Convert to JSON string
        task_model_str = json.dumps(task_model, ensure_ascii=False)

        # Attempt to publish the message to the network
        if await self.publish_message(task_model_str, INPUT_CONTENT_TOPIC):
            # Save entire task as JSON in storage
            await self.storage.set_value(
                f"{task.id}", json.dumps(task.model_dump(), ensure_ascii=False)
            )

            # If it's a retried task, we store the mapping from old ID to new ID
            if is_retried and old_task_id:
                await self.kv.push(f":{old_task_id}", {"new_task_id": task.id})

    async def get_available_nodes(self, model_type: str) -> List[str]:
        """
        Retrieve a list of available nodes for a specified model type.

        Args:
            model_type (str): The type of model (e.g., "openai-gpt").

        Returns:
            List[str]: A list of available node addresses (hex strings, etc.).
        """
        # Try to load the available nodes list from storage
        try:
            available_nodes_raw = await self.storage.get_value(
                f"available-nodes-{model_type}"
            )
            return json.loads(available_nodes_raw) if available_nodes_raw else []
        except Exception as e:
            logger.error(f"Error getting available nodes for {model_type}: {e}")
            return []

    async def create_filter(
        self,
        tasks: List[Task],
        node_stats: Dict[str, float],
    ) -> Union[
        Tuple[None, None, None],
        Tuple[List[str], List[Dict[str, Union[int, str]]], List[List[str]]],
    ]:
        """
        Create Bloom filters and map tasks to nodes for load distribution.

        Args:
            tasks (List[Task]): List of tasks to distribute.
            node_stats (Dict[str, float]): Mapping from node to some performance score.

        Returns:
            Union[
                Tuple[None, None, None],
                Tuple[
                    List[str],               # picked_nodes
                    List[Dict[str, Union[int, str]]],  # bloom filter parameters
                    List[List[str]]          # node_models
                ]
            ]:
            Returns None, None, None if no suitable nodes are available.
        """
        # Gather all unique models requested by tasks
        requested_models = list(
            set(
                x.value if isinstance(x, Model) else x
                for task in tasks
                for x in task.models
            )
        )

        # Fetch all available nodes for each requested model
        all_model_nodes = {}
        for model in requested_models:
            nodes = await self.get_available_nodes(model)
            if nodes:
                all_model_nodes[model] = nodes

        # If no nodes are available for the requested models, return early
        if not all_model_nodes:
            return None, None, None

        # Build a combined dictionary of node stats for all relevant models
        stats_for_model_nodes: Dict[str, float] = {}
        seen_nodes = set()

        for model, nodes in all_model_nodes.items():
            for node in nodes:
                # Avoid re-processing the same node
                if node in seen_nodes:
                    continue
                seen_nodes.add(node)

                # Find matching stat; fallback to default of 0.5 if not found
                node_stat = node_stats.get(node, 0.5)
                stats_for_model_nodes[node] = node_stat

        # If the total number of nodes * batch size is fewer than tasks, it's insufficient
        if len(stats_for_model_nodes) * COMPUTE_NODE_BATCH_SIZE < len(tasks):
            logger.debug("Not enough nodes available to handle all tasks.")
            return None, None, None

        # Use a node selection strategy to get a distribution of nodes
        selected_nodes = select_nodes(stats_for_model_nodes, len(tasks))

        # Count frequency of each node in the selection
        node_frequencies: Dict[str, int] = {}
        for node in selected_nodes:
            node_frequencies[node] = node_frequencies.get(node, 0) + 1

        # Calculate weighted scores = base score * frequency
        weighted_scores = {
            node: stats_for_model_nodes[node] * freq
            for node, freq in node_frequencies.items()
        }

        # Pick top N nodes by weighted score, where N = number of tasks
        # This ensures high performance nodes are selected
        sorted_nodes = sorted(
            weighted_scores.items(), key=lambda x: x[1], reverse=True
        )[: len(tasks)]
        picked_nodes = [node for node, _ in sorted_nodes]

        # Sample again with these top nodes to refine distribution
        sampled_stats = {node: stats_for_model_nodes[node] for node in picked_nodes}
        final_nodes = select_nodes(sampled_stats, len(tasks))

        # Prepare the Bloom filters and associated model for each node
        filters = []
        node_models = []
        for node in final_nodes:
            # Create a BloomFilter with size and error rate
            bf = BloomFilter(len(node) * 2 + 1, 0.001)
            bf.add(bytes.fromhex(node))
            filters.append({"hex": bf.get_bytes().hex(), "hashes": bf.hashes()})

            # Identify which models a node supports
            supported_models = [
                m for m, node_list in all_model_nodes.items() if node in node_list
            ]

            # Pick a random model out of the supported set
            if supported_models:
                random_model = random.choice(supported_models)
            else:
                # Fallback: if no supported model, skip or handle error
                random_model = "unknown"

            # Each node could be assigned a model list, though we pick just one
            node_models.append([random_model])

        logger.debug(f"Selected nodes: {final_nodes}")
        return final_nodes, filters, node_models

    async def add_peer_ids(self, peer_id_map: Dict[str, str]) -> None:
        """
        Add public keys to the task manager.

        Args:
            peer_id_map (Dict[str, str]): A dictionary mapping node addresses to public keys.

        Returns:
            None
        """
        try:
            for node, peer_id in peer_id_map.items():
                await self.storage.set_value(f"{node}:peer_id", peer_id)
        except Exception as e:
            logger.error(f"Error adding public keys: {e}")

    async def add_available_nodes(self, node_model: NodeModel, model_type: str) -> bool:
        """
        Store a list of available nodes for a given model type in storage.

        Args:
            node_model (NodeModel): The node model containing a list of node addresses.
            model_type (str): The type of model (e.g., "openai-gpt").

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Persist the node list in storage
            await self.storage.set_value(
                f"available-nodes-{model_type}",
                json.dumps(node_model.nodes, ensure_ascii=False),
            )
            return True
        except Exception as e:
            logger.error(f"Error adding available nodes: {e}")
            return False


def parse_json(
    text: Union[str, List[str]]
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse JSON from a string or a list of strings, handling different text formats.

    Supports:
    - Raw JSON
    - JSON in code blocks (```)
    - JSON in <JSON> tags
    - Lists of JSON strings

    Args:
        text (Union[str, List[str]]): Text or list of texts containing JSON.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: Parsed JSON as dict or list of dicts.

    Raises:
        ValueError: If JSON parsing fails.
    """

    def _parse_single_json(raw_str: str) -> Dict[str, Any]:
        """
        Extract valid JSON from raw_str, handling embedded code blocks or <JSON> tags.

        Args:
            raw_str (str): A string potentially containing embedded JSON.

        Returns:
            Dict[str, Any]: The parsed JSON object.

        Raises:
            ValueError: If JSON is invalid or irreparable.
        """
        # Possible patterns for extracting JSON
        patterns = [
            r"```(?:JSON)?\s*(.*?)\s*```",
            r"<JSON>\s*(.*?)\s*</JSON>",
        ]

        json_text = raw_str
        # Attempt regex extraction for code block or <JSON> tag
        for pattern in patterns:
            match = re.search(pattern, raw_str, re.DOTALL | re.IGNORECASE)
            if match:
                json_text = match.group(1)
                break

        # Attempt repair and parse
        try:
            return repair_json(json_text, return_objects=True)
        except json.JSONDecodeError as e:
            # Raise an error if the repair fails
            raise ValueError(f"Invalid JSON format: {json_text}") from e

    if isinstance(text, list):
        # If we receive a list of JSON strings, parse each individually
        return [_parse_single_json(item) for item in text]
    else:
        # Otherwise parse the single input
        return _parse_single_json(text)
