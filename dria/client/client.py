import json
import asyncio
import base64
import logging
import os
import signal
import time
from typing import Any, List, Optional, Dict, Union, Tuple

from Crypto.Hash import keccak
from dria_workflows import Workflow
from tqdm import tqdm

from dria.client.monitor import Monitor
from dria.constants import (
    OUTPUT_CONTENT_TOPIC,
    RETURN_DEADLINE,
    MONITORING_INTERVAL,
    FETCH_INTERVAL,
    SCORING_BATCH_SIZE,
    TASK_TIMEOUT,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import Task, TaskResult
from dria.models.enums import (
    FunctionCallingModels,
    OllamaModels,
    OpenAIModels,
    CoderModels,
    GeminiModels,
    OpenRouterModels,
    SmallModels,
    MidModels,
    LargeModels,
)
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utils import logger
from dria.utils.ec import (
    get_truthful_nodes,
    generate_task_keys,
    recover_public_key,
    uncompressed_public_key,
)
from dria.utils.node_evaluations import evaluate_nodes
from dria.utils.task_utils import TaskManager


class Dria:
    """
    Client SDK for interacting with the Dria distributed AI system.

    Provides high-level methods for:
    - Submitting AI tasks to the network
    - Retrieving task results
    - Managing background monitoring and polling
    - Handling node retries
    """

    DEADLINE_MULTIPLIER: int = 10

    def __init__(
        self,
        rpc_token: Optional[str] = None,
        api_mode: bool = False,
        log_level=logging.INFO,
    ):
        """
        Initialize the Dria client.

        Args:
            rpc_token (Optional[str]): Authentication token for RPC. Falls back to DRIA_RPC_TOKEN env var.
            api_mode (bool): If True, runs in API mode without cleanup of monitoring/polling.
        """
        logging.getLogger("dria").setLevel(log_level)
        self.rpc = RPCClient(auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN"))
        self.storage = Storage()
        self.kv = KeyValueQueue()
        self.task_manager = TaskManager(self.storage, self.rpc, self.kv)
        self.background_tasks: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        self.api_mode = api_mode
        self.stats = {}
        self.metrics = []

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle termination signals by initiating graceful shutdown."""
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        asyncio.create_task(self._set_shutdown())

    async def _set_shutdown(self):
        """Set shutdown event asynchronously"""
        self.shutdown_event.set()

    def set_api_mode(self, api_mode: bool) -> None:
        """
        Set client API mode.

        Args:
            api_mode (bool): If True, runs in API mode without cleanup
        """
        self.api_mode = api_mode

    async def initialize(self) -> None:
        """Initialize background monitoring and polling tasks."""
        if self.background_tasks:
            if not self.background_tasks.done():
                logger.info("Background tasks already running")
                return
        self.background_tasks = asyncio.create_task(self._start_background_tasks())

    async def _start_background_tasks(self) -> None:
        """Start and manage background monitoring and polling tasks."""
        monitor = Monitor(self.storage, self.rpc, self.kv)

        try:
            while not self.shutdown_event.is_set():
                try:
                    await asyncio.gather(monitor.run(), self.poll())
                    await asyncio.sleep(MONITORING_INTERVAL)
                except Exception as e:
                    raise Exception(f"Error in monitoring process: {e}")
            raise Exception("Shutdown event received")

        except asyncio.CancelledError:
            logger.info("Background tasks cancelled.")
        except Exception as e:
            if not self.api_mode:
                await self.run_cleanup(forced=True)
                raise Exception(f"Error in background tasks: {e}")

    async def _run_health_check(self) -> None:
        """Run periodic RPC health checks."""
        while not self.shutdown_event.is_set():
            try:
                is_healthy = await self.rpc.health_check()
                if not is_healthy:
                    raise Exception("RPC server is not healthy. Exiting...")
            except Exception as e:
                raise Exception(f"Error in health check process: {e}")
            await asyncio.sleep(10)
        raise Exception("Received signal for closing...")

    async def run_cleanup(self, forced: bool = False) -> None:
        """
        Clean up background tasks.

        Args:
            forced (bool): If True, forces cleanup regardless of API mode
        """
        if not self.api_mode or forced:
            if self.background_tasks and not self.background_tasks.done():
                self.background_tasks.cancel()
                try:
                    await self.background_tasks
                except asyncio.CancelledError:
                    pass

    async def push(self, tasks: List[Task]) -> bool | None:
        """
        Submit a task to the network.

        Args:
            tasks (Task): Task to submit

        Returns:
            bool: True if successfully published

        Raises:
            TaskPublishError: If task publication fails
        """
        await self._check_function_calling_models(tasks)

        for idx, task in enumerate(tasks):
            # Generate valid task keys
            max_attempts = 20
            for attempt in range(max_attempts):
                task.private_key, task.public_key = generate_task_keys()
                if not task.public_key.startswith("0x0"):
                    break
            else:
                raise TaskPublishError(
                    f"Failed to generate valid keys for task {task.id} after {max_attempts} attempts."
                )
            tasks[idx] = task

        try:
            nodes, filters, models = None, None, None
            attempts = 0
            while nodes is None:
                if self.background_tasks.done():
                    return None
                if attempts % 20 == 0 and attempts != 0:
                    logger.info("Waiting for nodes to be available...")
                await asyncio.sleep(MONITORING_INTERVAL)
                nodes, filters, models = await self.task_manager.create_filter(
                    tasks, self.stats
                )
                attempts += 1

            selected_models = []
            for idx, i in enumerate(zip(nodes, filters, models)):
                tasks[idx].nodes = [i[0]]
                tasks[idx].filter = i[1]
                selected_models.append(i[2])
            await asyncio.gather(
                *[
                    self.task_manager.push_task(task, selected_models[idx])
                    for idx, task in enumerate(tasks)
                ]
            )
            logger.debug(f"Task successfully published")
            return True

        except Exception as e:
            raise TaskPublishError(f"Failed to publish task: {e}") from e

    async def fetch(
        self,
        pipeline: Optional[Any] = None,
        task: Union[Optional[Task], Optional[List[Task]]] = None,
        min_outputs: Optional[int] = None,
        timeout: int = TASK_TIMEOUT,
        is_disabled: bool = False,
    ) -> List[TaskResult]:
        """
        Fetch task results from storage.

        Args:
            pipeline (Optional[Any]): Pipeline to fetch results for
            task (Union[Optional[Task], Optional[List[Task]]]): Task(s) to fetch results for
            min_outputs (Optional[int]): Minimum number of outputs to fetch
            timeout (int): Fetch timeout in seconds
            is_disabled (bool): TQDM Display

        Returns:
            List[TaskResult]: List of task results

        Raises:
            ValueError: If neither pipeline nor task provided
        """
        if not pipeline and not task:
            raise ValueError("At least one of pipeline or task must be provided.")

        results: List[TaskResult] = []
        start_time = time.time()
        min_outputs = self._determine_min_outputs(task, min_outputs)

        with tqdm(
            total=min_outputs, desc="Fetching results...", disable=is_disabled
        ) as pbar:
            while len(results) < min_outputs and not self.shutdown_event.is_set():
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout > 0:
                    logger.debug(
                        f"Unable to fetch {min_outputs} outputs within {timeout} seconds."
                    )
                    break

                pipeline_id = (
                    getattr(pipeline, "pipeline_id", None) if pipeline else None
                )
                task_id = self._get_task_id(task)

                new_results, new_id_map = await self._fetch_results(
                    pipeline_id, task_id
                )

                results.extend(new_results.values())
                pbar.update(len(new_results))
                if task is not None:
                    if isinstance(task, str):
                        task = [task]
                    task = [t for t in task if t.id not in new_results.keys()]

                for key, value in new_id_map.items():
                    if isinstance(task, str):
                        task.id = value
                        break
                    else:
                        for t in task:
                            if t.id == key[1:]:
                                t.id = value

                if timeout == 0:
                    return results
                if not new_results:
                    await asyncio.sleep(FETCH_INTERVAL)

            return results

    @staticmethod
    def _determine_min_outputs(
        task: Union[Optional[Task], Optional[List[Task]]],
        min_outputs: Optional[int],
    ) -> int:
        """
        Determine minimum required outputs.

        Args:
            task: Task(s) to determine outputs for
            min_outputs: Requested minimum outputs

        Returns:
            int: Determined minimum outputs
        """
        if min_outputs is None:
            return len(task) if isinstance(task, list) else 1

        if isinstance(task, list) and min_outputs > len(task):
            logger.warning(f"min_outputs exceeds task count. Setting to {len(task)}")
            return len(task)
        elif not isinstance(task, list) and min_outputs > 1:
            logger.warning("min_outputs exceeds task count. Setting to 1")
            return 1
        return min_outputs

    @staticmethod
    def _get_task_id(
        task: Union[Optional[Task], Optional[List[Task]]]
    ) -> Union[None, str, List[str]]:
        """
        Get task ID(s) from task object(s).

        Args:
            task: Task object(s)

        Returns:
            Task ID(s) or None

        Raises:
            ValueError: If invalid task type
        """
        if task is None:
            return None
        elif isinstance(task, Task):
            return task.id
        elif isinstance(task, list):
            return [t.id for t in task]
        else:
            raise ValueError("Invalid task type. Expected None, Task, or List[Task].")

    async def _fetch_results(
        self,
        pipeline_id: Optional[str],
        task_id: Union[Optional[str], Optional[List[str]]],
    ) -> Tuple[Dict[str, TaskResult], Dict[str, str]]:
        """
        Fetch results for pipeline and/or tasks.

        Args:
            pipeline_id: Pipeline ID
            task_id: Task ID(s)

        Returns:
            Tuple of results dict and ID mapping dict
        """
        new_results: Dict[str, TaskResult] = {}
        new_id_map: Dict[str, str] = {}

        if pipeline_id:
            if task_id:
                if isinstance(task_id, str):
                    key = f"{pipeline_id}:{task_id}"
                    value = await self.kv.pop(key)
                    if value:
                        task_result = await self._create_task_result(task_id, value)
                        if task_result:
                            new_results[task_id] = task_result
                elif isinstance(task_id, list):
                    for tid in task_id:
                        key = f"{pipeline_id}:{tid}"
                        value = await self.kv.pop(key)
                        if value:
                            task_result = await self._create_task_result(tid, value)
                            if task_result:
                                new_results[tid] = task_result
            else:
                new_results = await self._fetch_pipeline_results(pipeline_id)
        elif task_id:
            if isinstance(task_id, str):
                new_results, new_ids = await self._fetch_task_results(task_id)
            elif isinstance(task_id, list):
                for tid in task_id:
                    new_res, new_ids = await self._fetch_task_results(tid)
                    new_results.update(new_res)
                    new_id_map.update(new_ids)

        return new_results, new_id_map

    async def _fetch_pipeline_results(self, pipeline_id: str) -> Dict[str, TaskResult]:
        """
        Fetch all results for a pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dict of task results
        """
        results: Dict[str, TaskResult] = {}
        for key in await self.kv.keys():
            if key.startswith(f"{pipeline_id}:"):
                value = await self.kv.pop(key)
                if value:
                    task_id = key.split(":", 1)[1]
                    task_result = await self._create_task_result(task_id, value)
                    if task_result:
                        results[task_id] = task_result
        return results

    async def _fetch_task_results(
        self, task_id: str
    ) -> Tuple[Dict[str, TaskResult], Dict[str, Any]]:
        """
        Fetch results for a specific task.

        Args:
            task_id: Task ID

        Returns:
            Tuple of results dict and new ID mapping
        """
        results: Dict[str, TaskResult] = {}
        new_ids = {}
        suffix = f":{task_id}"
        for key in await self.kv.keys():
            if key.endswith(suffix):
                value = await self.kv.peek(key)
                if value:
                    if "new_task_id" in value.keys():
                        new_ids[key] = value["new_task_id"]
                    else:
                        task_result = await self._create_task_result(task_id, value)
                        if task_result:
                            results[task_id] = task_result
        return results, new_ids

    async def _create_task_result(
        self, task_id: str, value: dict
    ) -> Optional[TaskResult]:
        """
        Create TaskResult object from raw data.

        Args:
            task_id: Task ID
            value: Raw result value

        Returns:
            TaskResult object or None

        Raises:
            ValueError: If task data invalid
        """
        try:
            task_data = json.loads(await self.storage.get_value(task_id))
        except (json.JSONDecodeError, TypeError):
            logger.debug(f"Invalid task data for task_id: {task_id}")
            return None

        step_name = await self._get_step_name(task_id)
        return TaskResult(
            id=task_id,
            step_name=step_name,
            result=value["result"],
            task_input=task_data["workflow"]["external_memory"],
            model=value["model"],
        )

    async def poll(self) -> None:
        """Poll output content topic for results."""
        try:
            topic_results = await self.rpc.get_content_topic(OUTPUT_CONTENT_TOPIC)
            if topic_results:
                await self._process_results(list(set(topic_results)))
        except Exception as e:
            raise Exception(f"Error fetching content topic: {e}")

    async def _process_results(self, topic_results: List[str]) -> None:
        """
        Process results from output content topic.

        Args:
            topic_results: Raw results from topic
        """
        current_time = int(time.time())
        current_ns = time.time_ns()

        signature = None
        for item in topic_results:
            try:
                decoded_item = base64.b64decode(item).decode("utf-8")
                try:
                    result = json.loads(decoded_item)
                except json.JSONDecodeError:
                    signature, metadata_json = decoded_item[:130], decoded_item[130:]
                    result = json.loads(metadata_json)
                identifier, rpc_auth = result["taskId"].split("--")
                task_data = await self.storage.get_value(identifier)
                if not task_data:
                    logger.debug(f"Task data not found for identifier: {identifier}")
                    continue

                task_data = json.loads(task_data)

                if "new_task_id" in task_data.keys():
                    continue

                try:
                    task = Task(**task_data)
                except Exception as e:
                    logger.error(f"Error validating task data: {e}", exc_info=True)
                    continue

                if task.processed:
                    logger.debug(f"Task {task.id} already processed. Skipping.")
                    continue

                task.processed = True
                await self.storage.set_value(identifier, json.dumps(task.dict()))
                if "error" in result:

                    public_key = recover_public_key(
                        bytes.fromhex(signature), metadata_json.encode()
                    )
                    public_key = uncompressed_public_key(public_key)
                    address = (
                        keccak.new(digest_bits=256)
                        .update(public_key[1:])
                        .digest()[-20:]
                        .hex()
                    )
                    if address not in task.nodes:
                        logger.debug(f"{address} not in task nodes")
                        continue
                    try:
                        logger.debug(
                            f"ID: {identifier} {result['error'].split('Workflow execution failed: ')[1]}. Task retrying.."
                        )
                    except IndexError:
                        logger.debug(
                            f"ID: {identifier} {result['error']}. Task retrying.."
                        )
                    if "stats" in result.keys():
                        l = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (
                                current_ns - result["stats"]["publishedAt"]
                            )
                            / 1e9,
                            "execution_time": (result["stats"]["executionTime"]) / 1e9,
                            "receive_latency": -(
                                task_data["created_ts"] - result["stats"]["receivedAt"]
                            )
                            / 1e9,
                            "roundtrip": (current_ns - task_data["created_ts"]) / 1e9,
                        }
                        if "error" in result:
                            l["error"] = True
                        logger.debug(f"Metrics: {l}")
                        self.metrics.append(l)
                    workflow = await self.storage.get_value(f"{task.id}:workflow")
                    t = Task(
                        id=task.id,
                        workflow=workflow,
                        models=task.models,
                        step_name=task.step_name,
                        pipeline_id=task.pipeline_id,
                    )
                    asyncio.create_task(self.push([t]))
                    continue

                if self._is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(
                        task, result, rpc_auth
                    )
                    if processed_result is None:
                        logger.debug(f"Address: {address}    not valid in nodes.")
                        continue

                    pipeline_id = task.pipeline_id or ""
                    if "stats" in result.keys():
                        l = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (
                                current_ns - result["stats"]["publishedAt"]
                            )
                            / 1e9,
                            "execution_time": (result["stats"]["executionTime"]) / 1e9,
                            "receive_latency": -(
                                task_data["created_ts"] - result["stats"]["receivedAt"]
                            )
                            / 1e9,
                            "roundtrip": (current_ns - task_data["created_ts"]) / 1e9,
                        }
                        if "error" in result:
                            l["error"] = True
                        logger.debug(f"Task id: {identifier}, Metrics: {l}")
                        self.metrics.append(l)
                    await self.kv.push(
                        f"{pipeline_id}:{identifier}",
                        {"result": processed_result, "model": result["model"]},
                    )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error processing item: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error processing item: {e}", exc_info=True)

    async def execute(
        self, task: Union[Task, List[Task]], timeout: int = 300
    ) -> list[TaskResult] | None:
        """
        Execute task(s) and get results.

        Args:
            task: Task(s) to execute
            timeout: Execution timeout in seconds

        Returns:
            List of task results

        Raises:
            ValueError: If invalid task type
        """
        if not task:
            raise ValueError(
                "Cannot execute empty task list. At least one Task object must be provided for execution."
            )
        await self.initialize()

        if isinstance(task, Task):
            tasks = [task]
        elif isinstance(task, list):
            if not all(isinstance(t, Task) for t in task):
                raise ValueError("All elements must be Task objects")
            tasks = task
        else:
            raise ValueError("Invalid task type. Expected Task or List[Task].")

        try:
            tasks_ = [t.__deepcopy__() for t in tasks]
            batched_tasks = [
                tasks_[i : i + SCORING_BATCH_SIZE]
                for i in range(0, len(tasks_), SCORING_BATCH_SIZE)
            ]
            results = []
            for batch_tasks in batched_tasks:
                success = await self.push(batch_tasks)
                if success is False:
                    return None
                results.extend(await self.fetch(task=batch_tasks, timeout=timeout))
                self.stats = evaluate_nodes(self.metrics, self.stats)
                self.metrics = []

            return results
        except Exception as e:
            logger.error(f"Error during task execution: {str(e)}")
            raise

    @staticmethod
    def _is_task_valid(task: Task, current_time: int) -> bool:
        """
        Check if task is within deadline.

        Args:
            task: Task to validate
            current_time: Current timestamp

        Returns:
            bool: True if valid
        """
        task_deadline = int(task.deadline)
        if task_deadline == 0:
            logger.debug(f"Task {task.id} has no deadline. Skipping.")
            return False
        if (current_time - task_deadline) > RETURN_DEADLINE:
            logger.debug(f"Task {task.id} deadline exceeded. Skipping.")
            return False
        return True

    async def get_retried_tasks(self, task_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Get tasks that need to be retried.

        Args:
            task_ids: List of task IDs to check

        Returns:
            Dict mapping original task IDs to new task IDs (None if no new task ID)
        """
        task_map = {}
        
        for task_id in task_ids:
            current_task_id = task_id
            while True:
                task_metadata = await self.kv.peek(f":{current_task_id}")
                if not task_metadata:
                    task_map[task_id] = current_task_id
                    break

                try:
                    new_task_id = task_metadata.get("new_task_id")
                    if not new_task_id:
                        task_map[task_id] = current_task_id
                        break
                    current_task_id = new_task_id
                except json.JSONDecodeError:
                    task_map[task_id] = None
                    break
                    
        return task_map

    async def _get_step_name(self, task_id: str) -> str:
        """
        Get step name from task metadata.

        Args:
            task_id: Task ID

        Returns:
            Step name

        Raises:
            ValueError: If metadata invalid/missing
        """
        task_metadata = await self.storage.get_value(task_id)
        if task_metadata:
            try:
                return json.loads(task_metadata)["step_name"]
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing task metadata for task_id {task_id}: {e}")
                raise ValueError(f"Invalid task metadata for task id: {task_id}") from e
        raise ValueError(f"Task metadata not found for task id: {task_id}")

    @staticmethod
    async def _check_function_calling_models(tasks: List[Task]) -> None:
        """
        Validate models for function calling tasks.

        Args:
            tasks: Task to validate

        Raises:
            ValueError: If no supported models found
        """
        for task in tasks:
            if isinstance(task.workflow, Workflow):
                has_function_calling = any(
                    t.operator == "function_calling" for t in task.workflow.tasks
                )
            else:
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
                elif model == "gemini":
                    model_list.extend(model.value for model in GeminiModels)
                elif model == "openrouter":
                    model_list.extend(model.value for model in OpenRouterModels)
                elif model == "small":
                    model_list.extend(model.value for model in SmallModels)
                elif model == "mid":
                    model_list.extend(model.value for model in MidModels)
                elif model == "large":
                    model_list.extend(model.value for model in LargeModels)
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
                            f"Model '{model}' not supported for function calling and will be removed."
                        )

                if not filtered_models:
                    supported_model_names = [
                        model.name for model in FunctionCallingModels
                    ]
                    raise ValueError(
                        f"No supported function calling models found for task. "
                        f"Supported models: {', '.join(supported_model_names)}"
                    )

            task.models = filtered_models
