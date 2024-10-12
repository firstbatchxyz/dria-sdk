import asyncio
import base64
import json
import os
import signal
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
from dria.models.enums import (
    FunctionCallingModels,
    OllamaModels,
    OpenAIModels,
    CoderModels,
)
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
        Initialize the Dria client with the given configuration.

        Args:
            rpc_token (Optional[str]): Authentication token for RPCClient. If not provided,
                                       it will attempt to use the DRIA_RPC_TOKEN environment variable.
        """
        self.rpc = RPCClient(auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN"))
        self.storage = Storage()
        self.task_manager = TaskManager(self.storage, self.rpc)
        self.kv = KeyValueQueue()
        self.background_tasks: Optional[asyncio.Task] = None
        self.blacklist: Dict[str, Dict[str, int]] = {}
        self.running_pipelines: List[str] = []
        self.shutdown_event = asyncio.Event()

        cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
        os.makedirs(cache_dir, exist_ok=True)

        self.blacklist_file = os.path.join(cache_dir, ".blacklist")
        self._load_blacklist()

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle SIGTERM and SIGINT signals."""
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.shutdown_event.set()

    def _load_blacklist(self) -> None:
        """Load the blacklist from file or create a new one if it doesn't exist."""
        try:
            with open(self.blacklist_file, "r") as f:
                self.blacklist = {}
                for line in f:
                    key, value = line.strip().split("|")
                    self.blacklist[key] = eval(value)
        except FileNotFoundError:
            self.blacklist = {}
            self._save_blacklist()

    def _save_blacklist(self) -> None:
        """Save the current blacklist to file."""
        with open(self.blacklist_file, "w") as f:
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

    def initialize_pipeline(self, pipeline_id: str) -> None:
        """
        Initialize a pipeline by adding its ID to the list of running pipelines.

        Args:
            pipeline_id (str): The ID of the pipeline to initialize.
        """
        self.running_pipelines.append(pipeline_id)

    def remove_pipeline(self, pipeline_id: str) -> None:
        """
        Remove a pipeline from the list of running pipelines.

        Args:
            pipeline_id (str): The ID of the pipeline to remove.
        """
        if pipeline_id in self.running_pipelines:
            self.running_pipelines.remove(pipeline_id)

    def flush_blacklist(self) -> None:
        """Clear the blacklist and save the empty state to file."""
        self.blacklist = {}
        self._save_blacklist()

    async def initialize(self) -> None:
        """Initialize background tasks for monitoring and polling."""
        self.background_tasks = asyncio.create_task(self._start_background_tasks())

    async def _start_background_tasks(self) -> None:
        """Start and manage background tasks for monitoring and polling."""
        try:
            await asyncio.gather(self._run_monitoring(), self.poll())
        except asyncio.CancelledError:
            logger.info("Background tasks cancelled.")
        except Exception as e:
            await self.run_cleanup("*")
            raise Exception(f"Error in background tasks: {e}")

    async def _run_monitoring(self) -> None:
        """Run the monitoring process to track task statuses."""
        await self.rpc.initialize()
        monitor = Monitor(self.storage, self.rpc)
        while not self.shutdown_event.is_set():
            try:
                await monitor.run()
            except Exception as e:
                raise Exception(f"Error in monitoring process: {e}")
            await asyncio.sleep(MONITORING_INTERVAL)
        raise Exception("Received signal for closing...")

    async def run_cleanup(self, pipeline_id: Optional[str] = None) -> None:
        """
        Run the cleanup process to remove expired tasks and pipelines.

        Args:
            pipeline_id (Optional[str]): The ID of the pipeline to clean up. If "*", cleans up all pipelines.
        """
        if pipeline_id:
            if pipeline_id == "*":
                self.running_pipelines.clear()
            else:
                self.remove_pipeline(pipeline_id)
        if not self.running_pipelines:
            if self.background_tasks and not self.background_tasks.done():
                self.background_tasks.cancel()
                try:
                    await self.background_tasks
                except asyncio.CancelledError:
                    pass
            await self.rpc.close()

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
            if not task.public_key.startswith(
                "0x0"
            ):  # It should not start with 0 for encoding reasons
                break
        else:
            raise TaskPublishError(
                f"Failed to generate valid keys for task {task.id} after {max_attempts} attempts."
            )

        try:
            success, nodes = await self.task_manager.push_task(task, self.blacklist)
            if success:
                await self._update_blacklist(nodes)
                logger.info(
                    f"Task {task.id} successfully published. Step: {task.step_name}"
                )
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
            wait_time = self.DEADLINE_MULTIPLIER * 60 * (4 ** (node_entry["count"] - 1))
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
        timeout: int = 30,
    ) -> List[TaskResult]:
        """
        Fetch task results from storage based on pipelines and/or task.

        Args:
            pipeline (Optional[Any]): The pipeline.
            task (Union[Optional[Task], Optional[List[Task]]]): The task or list of tasks.
            min_outputs (Optional[int]): The minimum number of outputs to fetch.
            timeout (int): Timeout of fetch process in seconds.

        Returns:
            List[TaskResult]: A list of fetched results.

        Raises:
            ValueError: If both pipeline and task are None.
        """
        if not pipeline and not task:
            raise ValueError("At least one of pipeline or task must be provided.")

        results: List[TaskResult] = []
        start_time = time.time()
        min_outputs = self._determine_min_outputs(task, min_outputs)

        while len(results) < min_outputs and not self.shutdown_event.is_set():
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                if timeout > 0:
                    logger.debug(
                        f"Unable to fetch {min_outputs} outputs within {timeout} seconds."
                    )
                    break

            pipeline_id = getattr(pipeline, "pipeline_id", None) if pipeline else None
            task_id = self._get_task_id(task)

            new_results = self._fetch_results(pipeline_id, task_id)
            results.extend(new_results)

            if timeout == 0:
                return results
            if not new_results:
                await asyncio.sleep(FETCH_INTERVAL)

        return results

    def _determine_min_outputs(
        self,
        task: Union[Optional[Task], Optional[List[Task]]],
        min_outputs: Optional[int],
    ) -> int:
        """
        Determine the minimum number of outputs to fetch based on the task and provided min_outputs.

        Args:
            task (Union[Optional[Task], Optional[List[Task]]]): The task or list of tasks.
            min_outputs (Optional[int]): The provided minimum number of outputs.

        Returns:
            int: The determined minimum number of outputs.
        """
        if min_outputs is None:
            if isinstance(task, list):
                return len(task)
            else:
                return 1
        else:
            if isinstance(task, list) and min_outputs > len(task):
                logger.warning(
                    f"min_outputs is greater than the number of tasks. Setting min_outputs to {len(task)}"
                )
                return len(task)
            elif not isinstance(task, list) and min_outputs > 1:
                logger.warning(
                    "min_outputs is greater than the number of tasks. Setting min_outputs to 1"
                )
                return 1
            else:
                return min_outputs

    def _get_task_id(
        self, task: Union[Optional[Task], Optional[List[Task]]]
    ) -> Union[None, str, List[str]]:
        """
        Get the task ID or list of task IDs from the provided task(s).

        Args:
            task (Union[Optional[Task], Optional[List[Task]]]): The task or list of tasks.

        Returns:
            Union[None, str, List[str]]: The task ID, list of task IDs, or None.

        Raises:
            ValueError: If the task is of an invalid type.
        """
        if task is None:
            return None
        elif isinstance(task, Task):
            return task.id
        elif isinstance(task, list):
            return [t.id for t in task]
        else:
            raise ValueError("Invalid task type. Expected None, Task, or List[Task].")

    def _fetch_results(
        self,
        pipeline_id: Optional[str],
        task_id: Union[Optional[str], Optional[List[str]]],
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
            model=value["model"],
        )

    async def poll(self) -> None:
        """Continuously process tasks from the output content topic."""
        while not self.shutdown_event.is_set():
            try:
                topic_results = await self.rpc.get_content_topic(OUTPUT_CONTENT_TOPIC)
                if topic_results:
                    await self._process_results(list(set(topic_results)))
                else:
                    logger.debug("No results found in the output content topic.")
            except Exception as e:
                raise Exception(f"Error fetching content topic: {e}")
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

                if "error" in result:
                    logger.info(f"Error in result: {result['error']}. Task retrying..")
                    await self._handle_error_type(task, result["error"])
                    asyncio.create_task(self.push(task))
                    continue

                if self._is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(task, result)

                    if processed_result == "":
                        logger.info(
                            "Task result is not valid, retrying with another node..."
                        )
                        asyncio.create_task(self.push(task))
                        continue
                    else:
                        if address in self.blacklist:
                            self._remove_from_blacklist(address)
                    pipeline_id = task.pipeline_id or ""
                    self.kv.push(
                        f"{pipeline_id}:{identifier}",
                        {"result": processed_result, "model": result["model"]},
                    )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error processing item: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error processing item: {e}", exc_info=True)

    async def execute(
        self, task: Union[Task, List[Task]], timeout: int = 30
    ) -> List[Any]:
        """
        Execute a task or list of tasks.

        Args:
            task (Union[Task, List[Task]]): The task or list of tasks to execute.
            timeout (int): Timeout for task execution in seconds.

        Returns:
            List[Any]: A list of task results.

        Raises:
            ValueError: If the task is not of type Task or List[Task].
        """
        await self.initialize()

        if isinstance(task, Task):
            tasks = [task]
        elif isinstance(task, list):
            if not all(isinstance(t, Task) for t in task):
                raise ValueError("All elements in the list must be of type Task.")
            tasks = task
        else:
            raise ValueError("Invalid task type. Expected Task or List[Task].")

        try:
            tasks_ = [t.__deepcopy__() for t in tasks]
            for t in tasks_:
                await self.push(t)

            results = await self.fetch(task=tasks_, timeout=timeout)
            return [i.result for i in results]
        except Exception as e:
            logger.error(f"Error during task execution: {str(e)}")
            raise
        finally:
            await self.run_cleanup()

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
        has_function_calling = any(
            t.get("operator") == "function_calling"
            for t in task.workflow.get("tasks", [])
        )
        supported_models = set(model.value for model in FunctionCallingModels)

        model_list = []
        for model in task.models:
            if model == "openai":
                model_list.extend(model.value for model in OpenAIModels)
            elif model == "ollama":
                model_list.extend(model.value for model in OllamaModels)
            elif model == "coder":
                model_list.extend(model.value for model in CoderModels)
            else:
                model_list.append(model)

        filtered_models = model_list
        if has_function_calling:
            filtered_models = [
                model for model in model_list if model in supported_models
            ]

            for model in model_list:
                if model not in supported_models:
                    logger.warning(
                        f"Model '{model}' is not supported for function calling and will be removed."
                    )

            if not filtered_models:
                supported_model_names = [model.name for model in FunctionCallingModels]
                raise ValueError(
                    f"No supported function calling models found for task. "
                    f"Supported models: {', '.join(supported_model_names)}"
                )

        task.models = filtered_models

    async def _handle_error_type(self, task: Task, error: str) -> None:
        """Handle the error type."""
        if "InvalidInput" in error:
            for address in task.nodes:
                self._remove_from_blacklist(address)
