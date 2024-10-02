import asyncio
import json
import random
import re
import secrets
import string
import time
from typing import List, Tuple, Any, Dict, Union, Optional

from dria.models.enums import Model
from fastbloom_rs import BloomFilter

from dria.constants import MONITORING_INTERVAL, INPUT_CONTENT_TOPIC, TASK_DEADLINE
from dria.db.storage import Storage
from dria.models import NodeModel, TaskModel, TaskInputModel, Task
from dria.models.exceptions import TaskFilterError, TaskPublishError
from dria.request import RPCClient
from dria.utils import str_to_base64
from dria.utils.logging import logger


class TaskManager:
    def __init__(self, storage: Storage, rpc=RPCClient):
        self.storage = storage
        self.rpc = rpc

    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Generate a random string of a given length.

        Args:
            length (int, optional): Length of the random string. Defaults to 32.

        Returns:
            str: Random string
        """
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    async def publish_message(self, task: str, content_topic: str) -> bool:
        """
        Publish a message to a content topic.

        Args:
            task (str): Task to publish
            content_topic (str): Content topic to publish to

        Returns:
            bool: True if the message was published successfully, False otherwise
        """
        try:
            success = await self.rpc.push_content_topic(data=str_to_base64(task), content_topic=content_topic)
            return success
        except Exception as e:
            raise TaskPublishError(f"Failed to publish task: {e}") from e

    async def prepare_task(self, task: Task, blacklist: Dict[str, Dict[str, int]]) -> tuple[dict[str, Any], Task]:
        """
        Prepare a task for publishing.

        Args:
            task (Task): Task to prepare
            blacklist: The blacklisted nodes

        Returns:
            Tuple[dict, dict]: Task model and task
        """
        task_id = self.generate_random_string()
        deadline = int(time.time_ns() + TASK_DEADLINE * 1e9)
        try:
            picked_nodes, task_filter = await self.create_filter(task.models, blacklist)
        except Exception as e:
            raise TaskFilterError(f"{task.id}: {e}") from e

        task.id = task_id
        task.deadline = deadline
        task.nodes = picked_nodes

        task_input = TaskInputModel(
            workflow=task.workflow,
            model=task.models,
        ).dict()
        return TaskModel(
            taskId=task_id,
            filter=task_filter,
            input=task_input,
            deadline=deadline,
            publicKey=task.public_key.lstrip("0x")
        ).dict(), task

    async def push_task(self, task: Task, blacklist: Dict[str, Dict[str, int]]) -> tuple[bool, Union[
        Optional[List[str]]]]:
        """
        Push a task to the content topic.

        Args:
            task (Task): Task to push
            blacklist: The blacklisted nodes

        Returns:
            bool: True if the task was pushed successfully, False otherwise
        """
        task_model, task = await self.prepare_task(task, blacklist)
        task_model_str = json.dumps(task_model, ensure_ascii=False)
        if await self.publish_message(task_model_str, INPUT_CONTENT_TOPIC):
            self.storage.set_value(f"{task.id}", json.dumps(task.dict(), ensure_ascii=False))
            return True, task.nodes
        return False, None

    def get_available_nodes(self, model_type: str) -> List[str]:
        """
        Get available nodes for a given model type.

        Args:
            model_type (str): Model type to get available nodes for

        Returns:
            List[str]: List of available nodes
        """
        try:
            available_nodes = self.storage.get_value(f"available-nodes-{model_type}")
            return json.loads(available_nodes) if available_nodes else []
        except Exception as e:
            logger.error(f"Error getting available nodes for {model_type}: {e}")
            return []

    async def create_filter(
            self,
            using_models: List[str],
            blacklist: Dict[str, Dict[str, int]],
            retry: int = 0
    ) -> Tuple[List[str], dict]:
        """
        Create a filter for a given task.

        Args:
            using_models (List[str]): List of models to use
            blacklist (Dict[str, Dict[str, int]]): Blacklist of nodes
            retry (int, optional): Retry count. Defaults to 0.

        Returns:
            Tuple[List[str], dict]: Picked nodes and filter
        """

        """
        # TODO: Add retry
        if retry > constants.MAX_RETRIES_FOR_AVAILABILITY:
            raise TaskFilterError(
                f"No available nodes for models {using_models}. Try with a different model or retry later."
            )
        """

        available_nodes = set()
        for model in using_models:
            available_nodes_for_model = self.get_available_nodes(model)
            filtered_nodes = [
                node for node in available_nodes_for_model
                if int(time.time()) > blacklist.get(node, {"deadline": 0})["deadline"]
            ]
            available_nodes.update(filtered_nodes)

        logger.debug(f"Currently available nodes: {available_nodes}")

        if not available_nodes:
            logger.info(f"No available nodes for models {using_models}")
            log_str = ""
            for model in Model:
                node_count = len(self.get_available_nodes(model.value))
                if node_count > 0:
                    log_str += f"\n{model.name}: {node_count} nodes"
            if log_str:
                logger.debug(f"Current network state:{log_str}")
            else:
                logger.debug("No active nodes in the network")
            await asyncio.sleep(MONITORING_INTERVAL)
            return await self.create_filter(using_models, blacklist, retry + 1)

        picked_nodes = random.sample(list(available_nodes), 1)

        for model in using_models:
            try:
                self.storage.remove_from_list(f"available-nodes-{model}", None, picked_nodes)
            except ValueError:
                logger.debug(
                    f"Node {picked_nodes} not found in available nodes for model {model}. Passing this node for remove request.")

        bf = BloomFilter(len(picked_nodes) * 2 + 1, 0.001)
        for node in picked_nodes:
            bf.add(bytes.fromhex(node))

        logger.debug(f"Sending to: {picked_nodes}")
        return picked_nodes, {"hex": bf.get_bytes().hex(), "hashes": bf.hashes()}

    def add_available_nodes(self, node_model: NodeModel, model_type: str) -> bool:
        """
        Add available nodes to the storage.

        Args:
            node_model (NodeModel): Node model to add
            model_type (str): Model type to add the nodes for

        Returns:
            bool: True if the nodes were added successfully, False otherwise
        """
        try:
            self.storage.set_value(f"available-nodes-{model_type}", json.dumps(node_model.nodes, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"Error adding available nodes: {e}")
            return False


def parse_json(text: Union[str, List]) -> Union[list[dict], dict]:
    """Parse the JSON text.

    Args:
        text (str): The text to parse.

    Returns:
        dict: JSON output.
    """

    def parse_single_json(t: str) -> Dict:
        json_content = re.search(r'<JSON>(.*?)</JSON>', t, re.DOTALL)
        if not json_content:
            cleaned_text = t.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                return {}

        json_text = re.sub(r'<[^>]+>', '', json_content.group(1)).strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return {}

    if isinstance(text, list):
        return [parse_single_json(item) for item in text]
    else:
        return parse_single_json(text)
