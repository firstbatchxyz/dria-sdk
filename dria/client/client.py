import asyncio
import base64
import datetime
import json
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
    ReasoningModels,
)
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utils import logger
from dria.utils.crypto import (
    get_truthful_nodes,
    generate_task_keys,
    recover_public_key,
    uncompressed_public_key,
)
from dria.utils.node_selection import evaluate_nodes
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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            # Clean up old instance
            if hasattr(cls._instance, "shutdown_event"):
                cls._instance.shutdown_event.set()
            if hasattr(cls._instance, "background_tasks"):
                if cls._instance.background_tasks:
                    cls._instance.background_tasks.cancel()
        cls._instance = super().__new__(cls)
        return cls._instance

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
        if not hasattr(self, "_initialized"):
            logging.getLogger("dria").setLevel(log_level)
            self.rpc = RPCClient(
                auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN")
            )
            self.storage = Storage()
            self.kv = KeyValueQueue()
            self.task_manager = TaskManager(self.storage, self.rpc, self.kv)
            self.background_tasks: Optional[asyncio.Task] = None
            self.shutdown_event = asyncio.Event()
            self.api_mode = api_mode
            self.stats: Dict[str, Any] = {}
            self.metrics: List[Any] = []

            # Register signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            self._initialized = True

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
                logger.debug("Background tasks already running")
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
        await _check_function_calling_models(tasks)

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
                if self.background_tasks and self.background_tasks.done():
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
            logger.debug("Task successfully published")
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
            is_disabled (bool): Whether to disable progress bar display

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
        last_update = time.time()

        with tqdm(
            total=min_outputs, desc="Fetching results...", disable=is_disabled
        ) as pbar:
            response_times = {}  # Track response time for each task

            while len(results) < min_outputs and not self.shutdown_event.is_set():
                current_time = time.time()
                elapsed_time = current_time - start_time

                # Check timeout
                if elapsed_time > timeout > 0:
                    logger.debug(
                        f"Unable to fetch {min_outputs} outputs within {timeout} seconds."
                    )
                    break

                # Monitor slow responses
                if response_times:
                    responded_tasks = set(response_times.keys())
                    all_tasks = set(t.id for t in task)
                    unresponsive_tasks = all_tasks - responded_tasks

                    if unresponsive_tasks:
                        unresponsive_durations = {
                            task_id: current_time - start_time
                            for task_id in unresponsive_tasks
                        }

                        if response_times and len(response_times) > 0.4 * min_outputs:
                            avg_response_time = sum(response_times.values()) / len(
                                response_times
                            )

                            # Adjust multiplier based on how close we are to min_outputs
                            response_ratio = len(response_times) / min_outputs
                            multiplier = 5 if response_ratio < 0.95 else 2

                            concerning_tasks = {
                                task_id: duration
                                for task_id, duration in unresponsive_durations.items()
                                if duration > avg_response_time * multiplier
                            }

                            if concerning_tasks:
                                logger.debug(avg_response_time)
                                return results

                # Fetch new results
                pipeline_id = (
                    getattr(pipeline, "pipeline_id", None) if pipeline else None
                )
                task_id = self._get_task_id(task)
                new_results, new_id_map = await self._fetch_results(
                    pipeline_id, task_id
                )

                # Process new results
                for task_id in new_results:
                    response_times[task_id] = current_time - start_time
                results.extend(new_results.values())
                # Update progress bar
                if current_time - last_update >= 1.0:
                    pbar.n = len(results)
                    pbar.refresh()
                    last_update = current_time

                # Update task tracking
                if task is not None:
                    if isinstance(task, str):
                        task = [task]
                    task = [t for t in task if t.id not in new_results]

                # Update task IDs
                for key, value in new_id_map.items():
                    if isinstance(task, str):
                        task.id = value
                        break
                    else:
                        for t in task:
                            if t.id == key[1:]:
                                t.id = value

                # Handle immediate return case
                if timeout == 0:
                    return results

                # Sleep if no new results
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

        for item in topic_results:
            try:
                output = json.loads(item)
                msg = output["message"]
                signature = output["signature"]
                byte_sig = bytes.fromhex(signature)
                byte_sig = byte_sig + output["recovery_id"].to_bytes(1, byteorder="big")
                decoded_item = base64.b64decode(msg).decode("utf-8")
                result = json.loads(decoded_item)
                identifier, rpc_auth = result["taskId"].split("--")
                task_data = await self.storage.get_value(identifier)
                if not task_data or task_data is None:
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
                await self.storage.set_value(identifier, json.dumps(task.model_dump()))
                if "error" in result:
                    public_key = recover_public_key(byte_sig, msg.encode())
                    public_key = uncompressed_public_key(public_key)
                    address = (
                        keccak.new(digest_bits=256)
                        .update(bytes(public_key[1:]))
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
                    if "stats" in result:
                        current_ns = time.time_ns()
                        stats = result["stats"]
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                            "error": True,
                        }
                        
                        # Parse timestamps from ISO format strings
                        if "publishedAt" in stats:
                            try:
                                # Remove microseconds beyond 6 digits and handle Z timezone
                                timestamp = stats["publishedAt"]
                                if 'Z' in timestamp:
                                    # Split by Z and handle the microseconds part
                                    date_part, _ = timestamp.split('Z')
                                    if '.' in date_part:
                                        # Limit microseconds to 6 digits
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    timestamp = f"{date_part}+00:00"
                                published_dt = datetime.datetime.fromisoformat(timestamp)
                                published_ns = int(published_dt.timestamp() * 1e9)
                                metric_log["publish_latency"] = (current_ns - published_ns) / 1e9
                            except ValueError as e:
                                logger.debug(f"Error parsing publishedAt timestamp: {e}")
                            
                        if "executionStartedAt" in stats and "executionEndedAt" in stats:
                            try:
                                # Process start time
                                start_timestamp = stats["executionStartedAt"]
                                if 'Z' in start_timestamp:
                                    date_part, _ = start_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    start_timestamp = f"{date_part}+00:00"
                                start_dt = datetime.datetime.fromisoformat(start_timestamp)
                                
                                # Process end time
                                end_timestamp = stats["executionEndedAt"]
                                if 'Z' in end_timestamp:
                                    date_part, _ = end_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    end_timestamp = f"{date_part}+00:00"
                                end_dt = datetime.datetime.fromisoformat(end_timestamp)
                                
                                metric_log["execution_time"] = (end_dt - start_dt).total_seconds()
                            except ValueError as e:
                                logger.debug(f"Error parsing execution timestamps: {e}")
                            
                        if "receivedAt" in stats:
                            try:
                                # Process received time
                                received_timestamp = stats["receivedAt"]
                                if 'Z' in received_timestamp:
                                    date_part, _ = received_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    received_timestamp = f"{date_part}+00:00"
                                received_dt = datetime.datetime.fromisoformat(received_timestamp)
                                received_ns = int(received_dt.timestamp() * 1e9)
                                
                                created_ts = task_data["created_ts"]
                                if isinstance(created_ts, str):
                                    # Process created time
                                    if 'Z' in created_ts:
                                        date_part, _ = created_ts.split('Z')
                                        if '.' in date_part:
                                            main_part, micro_part = date_part.split('.')
                                            micro_part = micro_part[:6]
                                            date_part = f"{main_part}.{micro_part}"
                                        created_ts = f"{date_part}+00:00"
                                    created_dt = datetime.datetime.fromisoformat(created_ts)
                                    created_ns = int(created_dt.timestamp() * 1e9)
                                    metric_log["receive_latency"] = (received_ns - created_ns) / 1e9
                                    metric_log["roundtrip"] = (current_ns - created_ns) / 1e9
                            except ValueError as e:
                                logger.debug(f"Error parsing receivedAt timestamp: {e}")
                            
                        logger.debug(f"Metrics: {metric_log}")
                        self.metrics.append(metric_log)
                    if "Invalid prompt" in result["error"]:
                        logger.debug(
                            f"Prompt error for task {task.id}. Skipping this task."
                        )
                        pipeline_id = task.pipeline_id or ""
                        await self.kv.push(
                            f"{pipeline_id}:{identifier}",
                            {"result": None, "model": result["model"]},
                        )
                        continue
                    workflow = await self.storage.get_value(f"{task.id}:workflow")
                    t = Task(
                        id=task.id,
                        workflow=workflow,
                        models=task.models,
                        step_name=task.step_name,
                        pipeline_id=task.pipeline_id,
                        dataset_id=task.dataset_id,
                    )
                    asyncio.create_task(self.push([t]))
                    continue

                if self._is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(
                        task, result, msg, byte_sig
                    )
                    if processed_result is None:
                        logger.debug(f"Address: {address}    not valid in nodes.")
                        continue

                    pipeline_id = task.pipeline_id or ""
                    if "stats" in result:
                        current_ns = time.time_ns()
                        stats = result["stats"]
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                        }
                        
                        # Parse timestamps from ISO format strings
                        if "publishedAt" in stats:
                            try:
                                # Remove microseconds beyond 6 digits and handle Z timezone
                                timestamp = stats["publishedAt"]
                                if 'Z' in timestamp:
                                    # Split by Z and handle the microseconds part
                                    date_part, _ = timestamp.split('Z')
                                    if '.' in date_part:
                                        # Limit microseconds to 6 digits
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    timestamp = f"{date_part}+00:00"
                                published_dt = datetime.datetime.fromisoformat(timestamp)
                                published_ns = int(published_dt.timestamp() * 1e9)
                                metric_log["publish_latency"] = (current_ns - published_ns) / 1e9
                            except ValueError as e:
                                logger.debug(f"Error parsing publishedAt timestamp: {e}")
                            
                        if "executionStartedAt" in stats and "executionEndedAt" in stats:
                            try:
                                # Process start time
                                start_timestamp = stats["executionStartedAt"]
                                if 'Z' in start_timestamp:
                                    date_part, _ = start_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    start_timestamp = f"{date_part}+00:00"
                                start_dt = datetime.datetime.fromisoformat(start_timestamp)
                                
                                # Process end time
                                end_timestamp = stats["executionEndedAt"]
                                if 'Z' in end_timestamp:
                                    date_part, _ = end_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    end_timestamp = f"{date_part}+00:00"
                                end_dt = datetime.datetime.fromisoformat(end_timestamp)
                                
                                metric_log["execution_time"] = (end_dt - start_dt).total_seconds()
                            except ValueError as e:
                                logger.debug(f"Error parsing execution timestamps: {e}")
                            
                        if "receivedAt" in stats:
                            try:
                                # Process received time
                                received_timestamp = stats["receivedAt"]
                                if 'Z' in received_timestamp:
                                    date_part, _ = received_timestamp.split('Z')
                                    if '.' in date_part:
                                        main_part, micro_part = date_part.split('.')
                                        micro_part = micro_part[:6]
                                        date_part = f"{main_part}.{micro_part}"
                                    received_timestamp = f"{date_part}+00:00"
                                received_dt = datetime.datetime.fromisoformat(received_timestamp)
                                received_ns = int(received_dt.timestamp() * 1e9)
                                
                                created_ts = task_data["created_ts"]
                                if isinstance(created_ts, str):
                                    # Process created time
                                    if 'Z' in created_ts:
                                        date_part, _ = created_ts.split('Z')
                                        if '.' in date_part:
                                            main_part, micro_part = date_part.split('.')
                                            micro_part = micro_part[:6]
                                            date_part = f"{main_part}.{micro_part}"
                                        created_ts = f"{date_part}+00:00"
                                    created_dt = datetime.datetime.fromisoformat(created_ts)
                                    created_ns = int(created_dt.timestamp() * 1e9)
                                    metric_log["receive_latency"] = (received_ns - created_ns) / 1e9
                                    metric_log["roundtrip"] = (current_ns - created_ns) / 1e9
                            except ValueError as e:
                                logger.debug(f"Error parsing receivedAt timestamp: {e}")
                        
                        if "error" in result:
                            metric_log["error"] = True
                            
                        logger.debug(f"Task id: {identifier}, Metrics: {metric_log}")
                        self.metrics.append(metric_log)
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
                outputs = await self.fetch(task=batch_tasks, timeout=timeout)
                res = []
                for output in outputs:
                    if output.result is not None:
                        res.append(output)
                results.extend(res)
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
        task_deadline = task.deadline
        if task_deadline == 0:
            logger.debug(f"Task {task.id} has no deadline. Skipping.")
            return False
        
        # Convert ISO format string to timestamp if needed
        if isinstance(task_deadline, str):
            try:
                # Parse ISO format datetime string to datetime object
                dt = datetime.datetime.fromisoformat(task_deadline.replace('Z', '+00:00'))
                # Convert to timestamp
                task_deadline = int(dt.timestamp())
            except (ValueError, TypeError):
                logger.error(f"Invalid deadline format for task {task.id}: {task_deadline}")
                return False
                
        if (current_time - task_deadline) > RETURN_DEADLINE:
            logger.debug(f"Task {task.id} deadline exceeded. Skipping.")
            return False
        return True

    async def get_retried_tasks(self, task_ids: List[str]) -> Dict[str, str | None]:
        """
        Get tasks that need to be retried.

        Args:
            task_ids: List of task IDs to check

        Returns:
            Dict mapping original task IDs to new task IDs (None if no new task ID)
        """
        task_map: Dict[str, str | None] = {}

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
            elif model == "reasoning":
                model_list.extend(model.value for model in ReasoningModels)
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
                supported_model_names = [model.name for model in FunctionCallingModels]
                raise ValueError(
                    f"No supported function calling models found for task. "
                    f"Supported models: {', '.join(supported_model_names)}"
                )

        task.models = filtered_models
