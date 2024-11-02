import asyncio
import json
import random
import re
import secrets
import string
import time
from typing import List, Tuple, Any, Dict, Union

from fastbloom_rs import BloomFilter

from dria.constants import MONITORING_INTERVAL, INPUT_CONTENT_TOPIC, TASK_DEADLINE
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import NodeModel, TaskModel, TaskInputModel, Task
from dria.models.enums import Model
from dria.models.exceptions import TaskFilterError, TaskPublishError
from dria.request import RPCClient
from dria.utils import str_to_base64
from dria.utils.logging import logger


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

    async def prepare_task(
            self, task: Task, blacklist: Dict[str, Dict[str, int]]
    ) -> tuple[dict[str, Any], Task, str]:
        """
        Prepare task for publishing by generating ID, deadline and selecting nodes.

        Args:
            task: Task to prepare
            blacklist: Dict of blacklisted nodes

        Returns:
            Tuple of task model dict and prepared task

        Raises:
            TaskFilterError: If node selection fails
        """
        task.id = self.generate_random_string()
        deadline = int(time.time_ns() + TASK_DEADLINE * 1e9)

        try:
            picked_nodes, selected_model, task_filter = await self.create_filter(
                task.models, blacklist, task_id=task.id
            )
        except Exception as e:
            raise TaskFilterError(f"{task.id}: {e}") from e

        task.deadline = deadline
        task.nodes = picked_nodes

        task_input = TaskInputModel(
            workflow=task.workflow, model=[selected_model]
        ).dict()

        return (
            TaskModel(
                taskId=task.id,
                filter=task_filter,
                input=task_input,
                pickedNodes=picked_nodes,
                deadline=deadline,
                publicKey=task.public_key.lstrip("0x"),
                privateKey=task.private_key,
            ).dict(),
            task,
            selected_model,
        )

    async def push_task(
            self, task: Task, blacklist: Dict[str, Dict[str, int]]
    ) -> tuple[bool, list[str], str] | tuple[bool, None, None]:
        """
        Push prepared task to network.

        Args:
            task: Task to push
            blacklist: Dict of blacklisted nodes

        Returns:
            Tuple of (success bool, list of selected nodes if successful)
        """
        is_retried = False
        if task.id is not None:
            is_retried = True
            old_task_id = task.__deepcopy__().id

        task_model, task, selected_model = await self.prepare_task(task, blacklist)
        task_model_str = json.dumps(task_model, ensure_ascii=False)

        if await self.publish_message(task_model_str, INPUT_CONTENT_TOPIC):
            await self.storage.set_value(
                f"{task.id}", json.dumps(task.dict(), ensure_ascii=False)
            )
            if is_retried:
                await self.kv.push(f":{old_task_id}", {"new_task_id": task.id})
            return True, task.nodes, selected_model

        return False, None, None

    async def get_available_nodes(self, model_type: str) -> List[str]:
        """
        Get list of available nodes for specified model type.

        Args:
            model_type: Type of model to get nodes for

        Returns:
            List of available node addresses
        """
        try:
            available_nodes = await self.storage.get_value(f"available-nodes-{model_type}")
            return json.loads(available_nodes) if available_nodes else []
        except Exception as e:
            logger.error(f"Error getting available nodes for {model_type}: {e}")
            return []

    async def create_filter(
            self,
            using_models: List[str],
            blacklist: Dict[str, Dict[str, int]],
            task_id: str = "",
            retry: int = 0,
    ) -> Tuple[List[str], str, Dict]:
        """
        Create Bloom filter for node selection.

        Args:
            using_models: List of models needed
            blacklist: Dict of blacklisted nodes
            task_id: ID of task for logging
            retry: Number of retries attempted

        Returns:
            Tuple of (selected nodes, selected model, Bloom filter params)
        """
        # Get all available nodes for all models
        all_model_nodes = {}
        for model in using_models:
            nodes = await self.get_available_nodes(model)
            filtered_nodes = [
                node
                for node in nodes
                if int(time.time())
                   > blacklist.get(node + ":" + model, {"deadline": 0})["deadline"]
            ]
            if filtered_nodes:
                all_model_nodes[model] = filtered_nodes

        if not all_model_nodes:
            if retry % 20 == 0 and retry != 0:
                logger.info(f"Searching available nodes for task {task_id}")
                log_str = ""
                for model in Model:
                    node_count = len(await self.get_available_nodes(model.value))
                    if node_count > 0:
                        log_str += f" {model.name}: {node_count} nodes, "
                if log_str:
                    logger.debug(f"Current network state:{log_str}")
                else:
                    logger.debug("No active nodes in the network")
            await asyncio.sleep(MONITORING_INTERVAL)
            return await self.create_filter(
                using_models, blacklist, task_id=task_id, retry=retry + 1
            )

        selected_model = random.choice(list(all_model_nodes.keys()))
        picked_nodes = random.sample(all_model_nodes[selected_model], 1)

        for model in using_models:
            try:
                await self.storage.remove_from_list(
                    f"available-nodes-{model}", None, picked_nodes
                )
            except ValueError:
                logger.debug(
                    f"Node {picked_nodes} not found in available nodes for model {model}"
                )

        bf = BloomFilter(len(picked_nodes) * 2 + 1, 0.001)
        for node in picked_nodes:
            bf.add(bytes.fromhex(node))

        logger.debug(f"Selected nodes: {picked_nodes}")
        return (
            picked_nodes,
            selected_model,
            {"hex": bf.get_bytes().hex(), "hashes": bf.hashes()},
        )

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
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {json_text}") from e

    if isinstance(text, list):
        return [parse_single_json(item) for item in text]
    return parse_single_json(text)
