import asyncio
import base64
import json
import os
import time
from typing import Any, List, Optional, Dict, Union

from dria.client.monitor import Monitor
from dria.constants import (
    OUTPUT_CONTENT_TOPIC,
    RETURN_DEADLINE,
    MONITORING_INTERVAL,
    FETCH_INTERVAL,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import Task, TaskResult
from dria.models.enums import FunctionCallingModels, OllamaModels, OpenAIModels
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utils import logger
from dria.utils.ec import get_truthful_nodes, generate_task_keys
from dria.utils.task_utils import TaskManager


class Dria:
    """
    A client for interacting with the Dria system.

    This class provides methods for pushing tasks, fetching results,
    and managing background processes for monitoring and polling.
    """

    DEADLINE_MULTIPLIER: int = 10

    def __init__(self, rpc_token: Optional[str] = None):
        """
        Initialize the Dria with the given configuration.

        Args:
            rpc_token (str): Authentication token for RPCClient.
        """
        self.rpc = RPCClient(auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN"))
        self.storage = Storage()
        self.task_manager = TaskManager(self.storage, self.rpc)
        self.kv = KeyValueQueue()
        self.background_tasks: Optional[asyncio.Task] = None
        self.blacklist: Dict[str, Dict[str, int]] = {}

        cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
        os.makedirs(cache_dir, exist_ok=True)

        self.blacklist_file = os.path.join(cache_dir, '.blacklist')
        self._load_blacklist()

    def _load_blacklist(self):
        """Load the blacklist from file or create a new one if it doesn't exist."""
        try:
            with open(self.blacklist_file, 'r') as f:
                self.blacklist = {}
                for line in f:
                    key, value = line.strip().split('|')
                    self.blacklist[key] = eval(value)
        except FileNotFoundError:
            self.blacklist = {}
            self._save_blacklist()

    def _save_blacklist(self):
        """Save the current blacklist to file."""
        with open(self.blacklist_file, 'w') as f:
            for key, value in self.blacklist.items():
                f.write(f"{key}|{value}\n")

    def _remove_from_blacklist(self, address: str) -> None:
        """
        Remove an address from the blacklist and save the updated blacklist.

        Args:
            address (str): The address to remove from the blacklist.
        """
        if address in self.blacklist:
            del self.blacklist[address]
            self._save_blacklist()
            logger.info(f"Address {address} removed from blacklist.")
        else:
            logger.debug(f"Address {address} not found in blacklist.")

    def flush_blacklist(self):
        """Flush the blacklist to file."""
        self.blacklist = {}
        self._save_blacklist()

    async def initialize(self) -> None:
        """Initialize background tasks for monitoring and polling."""
        self.background_tasks = asyncio.create_task(self._start_background_tasks())

    async def _start_background_tasks(self) -> None:
        """Start and manage background tasks for monitoring and polling."""
        try:
            await asyncio.gather(
                self._run_monitoring(),
                self.poll()
            )
        except Exception:
            logger.error("Error in background tasks", exc_info=True)
            await asyncio.sleep(10)  # Retry after sleep

    async def _run_monitoring(self) -> None:
        """Run the monitoring process to track task statuses."""
        monitor = Monitor(self.storage, self.rpc)
        while True:
            try:
                await monitor.run()
            except Exception:
                logger.error("Error in monitoring", exc_info=True)

    async def push(self, task: Task) -> bool:
        """
        Process and publish a single task.

        Args:
            task (Task): The task to process and publish.

        Returns:
            bool: True if task was successfully published, False otherwise.

        Raises:
            TaskPublishError: If there's an error during task publication.
        """
        self._check_function_calling_models(task)

        max_attempts = 20
        for attempt in range(max_attempts):
            task.private_key, task.public_key = generate_task_keys()
            if task.public_key.startswith("0x0"):  # It should not start with 0 for encoding reasons
                continue
            break
        try:
            success, nodes = await self.task_manager.push_task(task, self.blacklist)
            if success:
                await self._update_blacklist(nodes)
                logger.info(f"Task {task.id} successfully published. Step: {task.step_name}")
                return True
            else:
                logger.error(f"Failed to publish task {task.id}.")
                return False
        except Exception as e:
            raise TaskPublishError(f"Failed to publish task {task.id}: {e}") from e

    async def _update_blacklist(self, nodes: List[str]) -> None:
        """
        Update the blacklist with the provided nodes.

        Args:
            nodes (List[str]): List of node identifiers to blacklist.
        """
        current_time = int(time.time())
        for node in nodes:
            node_entry = self.blacklist.get(node, {"count": 0})
            node_entry["count"] += 1
            wait_time = self.DEADLINE_MULTIPLIER * 60 * (2 ** (node_entry["count"] - 1))
            node_entry["deadline"] = current_time + wait_time
            self.blacklist[node] = node_entry
            logger.info(
                f"Address {node} added to blacklist with deadline at {node_entry['deadline']}."
            )

        self._save_blacklist()

    async def fetch(
            self,
            pipeline: Optional[Any] = None,
            task: Union[Optional[Task], Optional[List[Task]]] = None,
            min_outputs: Optional[int] = None,
            timeout: int = 300
    ) -> List[TaskResult]:
        """
        Fetch task results from storage based on pipeline and/or task.

        Args:
            pipeline (Optional[Pipeline]): The pipeline.
            task (Union[Optional[Task], Optional[List[Task]]]): The task.
            min_outputs (int): The minimum number of outputs to fetch.
            timeout (int): Timeout of fetch process

        Returns:
            List[TaskResult]: A list of fetched results.

        Raises:
            ValueError: If both pipeline and task are None.
        """
        if not pipeline and not task:
            raise ValueError("At least one of pipeline or task must be provided.")

        results: List[TaskResult] = []
        start_time = time.time()

        if min_outputs is None:
            if isinstance(task, list):
                min_outputs = len(task)
                if min_outputs > len(task) and isinstance(task, list):
                    logger.warning(f"min_outputs is greater than the number of task. Setting min_outputs to {len(task)}")
                    min_outputs = len(task)
            else:
                min_outputs = 1
                if min_outputs > 1:
                    logger.warning(f"min_outputs is greater than the number of task. Setting min_outputs to 1")
                    min_outputs = 1

        while len(results) < min_outputs:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                logger.warning(
                    f"Unable to fetch {min_outputs} outputs within {timeout} seconds."
                )
                break
            pipeline_id = pipeline.pipeline_id if pipeline and hasattr(pipeline, 'pipeline_id') else None

            if task is None:
                task_id = None
            elif isinstance(task, Task):
                task_id = task.id
            elif isinstance(task, list):
                task_id = [t.id for t in task]
            else:
                raise ValueError("Invalid task type. Expected None, Task, or List[Task].")

            new_results = self._fetch_results(pipeline_id, task_id)
            results.extend(new_results)

            if not new_results:
                await asyncio.sleep(FETCH_INTERVAL)

        return results

    def _fetch_results(
            self,
            pipeline_id: Optional[str],
            task_id: Union[Optional[str], Optional[List[str]]]
    ) -> List[TaskResult]:
        """
        Helper method to fetch results based on pipeline_id and/or task_id.

        Args:
            pipeline_id (Optional[str]): The ID of the pipeline.
            task_id (Union[Optional[str], Optional[List[str]]]): The ID or list of IDs of the task(s).

        Returns:
            List[TaskResult]: A list of fetched results.
        """
        new_results: List[TaskResult] = []

        if pipeline_id:
            if task_id:
                if isinstance(task_id, str):
                    key = f"{pipeline_id}:{task_id}"
                    value = self.kv.pop(key)
                    if value:
                        new_results.append(self._create_task_result(task_id, value))
                elif isinstance(task_id, list):
                    for tid in task_id:
                        key = f"{pipeline_id}:{tid}"
                        value = self.kv.pop(key)
                        if value:
                            new_results.append(self._create_task_result(tid, value))
            else:
                new_results = self._fetch_pipeline_results(pipeline_id)
        elif task_id:
            if isinstance(task_id, str):
                new_results = self._fetch_task_results(task_id)
            elif isinstance(task_id, list):
                for tid in task_id:
                    new_results.extend(self._fetch_task_results(tid))

        return new_results

    def _fetch_pipeline_results(self, pipeline_id: str) -> List[TaskResult]:
        """
        Fetch results for a specific pipeline.

        Args:
            pipeline_id (str): The ID of the pipeline.

        Returns:
            List[TaskResult]: A list of fetched results.
        """
        results: List[TaskResult] = []
        for key in self.kv.keys():
            if key.startswith(f"{pipeline_id}:"):
                value = self.kv.pop(key)
                if value:
                    task_id = key.split(":", 1)[1]
                    results.append(self._create_task_result(task_id, value))
        return results

    def _fetch_task_results(self, task_id: str) -> List[TaskResult]:
        """
        Fetch results for a specific task.

        Args:
            task_id (str): The ID of the task.

        Returns:
            List[TaskResult]: A list of fetched results.
        """
        results: List[TaskResult] = []
        suffix = f":{task_id}"
        for key in self.kv.keys():
            if key.endswith(suffix):
                value = self.kv.pop(key)
                if value:
                    results.append(self._create_task_result(task_id, value))
        return results

    def _create_task_result(self, task_id: str, value: dict) -> TaskResult:
        """
        Create a TaskResult object from task_id and value.

        Args:
            task_id (str): The ID of the task.
            value (dict): The result value.

        Returns:
            TaskResult: A TaskResult object.

        Raises:
            ValueError: If task data is not found or is invalid.
        """
        try:
            task_data = json.loads(self.storage.get_value(task_id))
        except json.JSONDecodeError:
            raise ValueError(f"Task data not found or invalid for task_id: {task_id}")

        step_name = self._get_step_name(task_id)
        return TaskResult(
            id=task_id,
            step_name=step_name,
            result=value["result"],
            task_input=task_data["workflow"]["external_memory"],
            model=value["model"]
        )

    async def poll(self) -> None:
        """Continuously process tasks from the output content topic."""
        while True:
            try:
                topic_results = await self.rpc.get_content_topic(OUTPUT_CONTENT_TOPIC)
                if topic_results:
                    await self._process_results(topic_results)
                else:
                    logger.debug("No results found in the output content topic.")
            except Exception as e:
                logger.exception("Error fetching content topic")
            finally:
                await asyncio.sleep(MONITORING_INTERVAL)

    async def _process_results(self, topic_results: List[str]) -> None:
        """
        Process results from the output content topic.

        Args:
            topic_results (List[str]): List of results from the output content topic.
        """
        current_time = int(time.time())

        for item in topic_results:
            try:
                decoded_item = base64.b64decode(item).decode("utf-8")
                result = json.loads(decoded_item)
                if "error" in result.keys():
                    logger.error(f"Error in result: {result['error']}")
                    continue
                identifier = result["taskId"]
                task_data = self.storage.get_value(identifier)
                if not task_data:
                    logger.debug(f"Task data not found for identifier: {identifier}")
                    continue

                task_data = json.loads(task_data)

                try:
                    task = Task(**task_data)
                except Exception as e:
                    logger.error(f"Error validating task data: {e}", exc_info=True)
                    continue

                if self._is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(task, result)
                    if processed_result is None:
                        logger.info("Task result is not valid, retrying with another node...")
                        asyncio.create_task(self.push(task))
                        continue
                    else:
                        if address in self.blacklist:
                            self._remove_from_blacklist(address)
                    pipeline_id = task.pipeline_id or ""
                    self.kv.push(f"{pipeline_id}:{identifier}", {"result": processed_result, "model": result["model"]})
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error processing item: {e}", exc_info=True)
            except Exception as e:
                logger.exception("Unexpected error processing item")

    @staticmethod
    def _is_task_valid(task: Task, current_time: int) -> bool:
        """
        Check if the task is valid based on its deadline.

        Args:
            task (Task): The task to check.
            current_time (int): The current time.

        Returns:
            bool: True if the task is valid, False otherwise.
        """
        task_deadline = int(task.deadline)
        if task_deadline == 0:
            logger.debug(f"Task {task.id} has no deadline set. Skipping.")
            return False
        if (current_time - task_deadline) > RETURN_DEADLINE:
            logger.debug(f"Task {task.id} deadline exceeded. Skipping.")
            return False
        return True

    def _get_step_name(self, task_id: str) -> str:
        """
        Get the step name from the task id.

        Args:
            task_id (str): The task ID.

        Returns:
            str: The step name.

        Raises:
            ValueError: If task metadata is not found or is invalid.
        """
        task_metadata = self.storage.get_value(task_id)
        if task_metadata:
            try:
                return json.loads(task_metadata)["step_name"]
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing task metadata for task_id {task_id}: {e}")
                raise ValueError(f"Invalid task metadata for task id: {task_id}") from e
        raise ValueError(f"Task metadata not found for task id: {task_id}")

    @staticmethod
    def _check_function_calling_models(task: Task) -> None:
        """
        Check if the task is using function calling models and validate the models.

        Args:
            task (Task): The task to check and validate.

        Raises:
            ValueError: If no supported function calling models are found for the task.
        """
        has_function_calling = any(t.get("operator") == "function_calling" for t in task.workflow.get("tasks", []))
        supported_models = set(model.value for model in FunctionCallingModels)

        model_list = []
        for model in task.models:
            if model == "openai":
                model_list.extend(model.value for model in OpenAIModels)
            elif model == "ollama":
                model_list.extend(model.value for model in OllamaModels)
            else:
                model_list.append(model)
        if has_function_calling:
            filtered_models = [model for model in model_list if model in supported_models]

            for model in model_list:
                if model not in supported_models:
                    logger.warning(f"Model '{model}' is not supported for function calling and will be removed.")

            task.models = filtered_models

            if not filtered_models:
                supported_model_names = [model.name for model in FunctionCallingModels]
                raise ValueError(f"No supported function calling models found for task. "
                                 f"Supported models: {', '.join(supported_model_names)}")
