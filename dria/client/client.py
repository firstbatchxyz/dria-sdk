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
from dria.datasets.utils import get_community_token
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
    MAX_RETRIES_FOR_AVAILABILITY: int = 5
    DEADLINE_MULTIPLIER: int = 10

    def __init__(
            self,
            rpc_token: Optional[str] = None,
            log_level=logging.INFO,
    ):
        """
        Initialize the Dria client.

        Args:
            rpc_token (Optional[str]): Authentication token for RPC. Falls back to DRIA_RPC_TOKEN env var.
            api_mode (bool): If True, runs in API mode without cleanup of monitoring/polling.
        """
        if not hasattr(self, '_initialized'):
            logging.getLogger("dria").setLevel(log_level)
            if rpc_token is None:
                rpc_token = get_community_token()
            self.rpc = RPCClient(auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN"))
            self.storage = Storage()
            self.kv = KeyValueQueue()
            self.task_manager = TaskManager(self.storage, self.rpc, self.kv)
            self.shutdown_event = asyncio.Event()
            self.stats: Dict[str, Any] = {}
            self.metrics: List[Any] = []
            self.monitoring = Monitor(self.storage, self.rpc, self.kv)

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
                if attempts % 20 == 0 and attempts != 0:
                    logger.info("Waiting for nodes to be available...")
                await self.check_heartbeat()
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

    async def fetch_cleaner(self, task_ids: List[str],
                            fetch_interval: int = FETCH_INTERVAL,
                            retries: int = 0) -> List[TaskResult]:
        """
        Recursively fetch and clean task results.

        Args:
            task_ids: List of task IDs to fetch results for
            fetch_interval: Fetch interval in seconds
            retries: Retry count

        Returns:
            List[TaskResult]: List of task results
        """
        if retries > self.MAX_RETRIES_FOR_AVAILABILITY:
            return []
        results = await self.poll(task_ids)
        if results is None:
            await asyncio.sleep(fetch_interval)
            return await self.fetch_cleaner(task_ids, fetch_interval ** 2, retries + 1)

        result_ids = {r.id for r in results}
        remaining_task_ids = [t for t in task_ids if t not in result_ids]

        if not remaining_task_ids:
            return results

        await asyncio.sleep(fetch_interval)
        remaining_results = await self.fetch_cleaner(remaining_task_ids, FETCH_INTERVAL, retries + 1)
        return results + remaining_results if remaining_results else results

    async def poll(self, task_ids: List[str]) -> list[TaskResult]:
        """Poll output content topic for results."""
        try:
            topic_results = await self.rpc.get_results(task_ids)
            if topic_results:
                results = await self._process_results(list(set(topic_results)))
                return results
        except Exception as e:
            raise Exception(f"Error fetching content topic: {e}")

    async def _process_results(self, topic_results: List[str]) -> List[TaskResult]:
        """
        Process results from output content topic.

        Args:
            topic_results: Raw results from topic

        Returns:
            List[TaskResult]: List of task results
        """
        current_time = int(time.time())
        results: List[TaskResult] = []
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
                await self.storage.set_value(identifier, json.dumps(task.dict()))
                if "error" in result:

                    public_key = recover_public_key(
                        bytes.fromhex(signature), metadata_json.encode()
                    )
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
                    if "stats" in result.keys():
                        current_ns = time.time_ns()
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (current_ns - result["stats"]["publishedAt"]) / 1e9,
                            "execution_time": result["stats"]["executionTime"] / 1e9,
                            "receive_latency": -(task_data["created_ts"] - result["stats"]["receivedAt"]) / 1e9,
                            "roundtrip": (current_ns - task_data["created_ts"]) / 1e9,
                            "error": True,
}
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
                        current_ns = time.time_ns()
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (current_ns - result["stats"]["publishedAt"]) / 1e9,
                            "execution_time": result["stats"]["executionTime"] / 1e9,
                            "receive_latency": -(task_data["created_ts"] - result["stats"]["receivedAt"]) / 1e9,
                            "roundtrip": (current_ns - task_data["created_ts"]) / 1e9,
                        }
                        if "error" in result:
                            metric_log["error"] = True
                        logger.debug(f"Task id: {identifier}, Metrics: {metric_log}")
                        self.metrics.append(metric_log)
                    await self.kv.push(
                        f"{pipeline_id}:{identifier}",
                        {"result": processed_result, "model": result["model"]},
                    )
                    results.append(TaskResult(
                        id=identifier,
                        step_name=task.step_name,
                        result=processed_result,
                        task_input=task.workflow["external_memory"],
                        model=result["model"]
                    ))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error processing item: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error processing item: {e}", exc_info=True)
        return results

    async def check_heartbeat(self) -> None:
        """
        Check if heartbeat is still valid.
        """
        if not await self.task_manager.should_monitor():
            return
        await self.monitoring.fetch_nodes()

    async def generate(self, instructions, singleton, models) -> List[TaskResult]:
        """
        Generate tasks from instructions and execute workflows.

        Args:
            instructions: List of instruction dictionaries
            singleton: Singleton class
            models: List of models

        Returns:
            Tuple of entry IDs and input IDs
        """
        tasks = []
        for task in instructions:
            tasks.append(Task(workflow=singleton.workflow(**task), models=models))
        
        return await self.execute(tasks)



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
                tasks_[i: i + SCORING_BATCH_SIZE]
                for i in range(0, len(tasks_), SCORING_BATCH_SIZE)
            ]
            results = []
            for batch_tasks in batched_tasks:
                success = await self.push(batch_tasks)
                if success is False:
                    return None

                outputs = await self.fetch_cleaner(task_ids=[t.id for t in batch_tasks])
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
        task_deadline = int(task.deadline)
        if task_deadline == 0:
            logger.debug(f"Task {task.id} has no deadline. Skipping.")
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
