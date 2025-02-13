import asyncio
import base64
import json
import signal
import time
from typing import Any, List, Dict, Union

from Crypto.Hash import keccak

from dria import TaskManager
from dria.constants import (
    FETCH_INTERVAL,
    SCORING_BATCH_SIZE,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.executor import Ping
from dria.models import Task, TaskResult
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utilities import Helper, evaluate_nodes, logger
from dria.utilities.crypto import (
    get_truthful_nodes,
    generate_task_keys,
    recover_public_key,
    uncompressed_public_key,
)


class TaskExecutor:
    """ """

    MAX_RETRIES_FOR_AVAILABILITY: int = 5
    DEADLINE_MULTIPLIER: int = 10

    def __init__(
        self,
        ping: Ping,
        rpc: RPCClient,
        storage: Storage,
        kv: KeyValueQueue,
        task_manager: TaskManager,
    ):
        """ """
        self.ping = ping
        self.rpc = rpc
        self.storage = storage
        self.kv = kv
        self.task_manager = task_manager
        self.shutdown_event = asyncio.Event()
        self.stats: Dict[str, Any] = {}
        self.metrics: List[Any] = []
        self.helper = Helper()

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
        await self.helper.check_function_calling_models(tasks)

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

    async def fetch(
        self,
        task_ids: List[str],
        fetch_interval: int = FETCH_INTERVAL,
        retries: int = 0,
    ) -> List[TaskResult]:
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
            return await self.fetch(task_ids, fetch_interval**2, retries + 1)

        result_ids = {r.id for r in results}
        remaining_task_ids = [t for t in task_ids if t not in result_ids]

        if not remaining_task_ids:
            return results

        await asyncio.sleep(fetch_interval)
        remaining_results = await self.fetch(
            remaining_task_ids, FETCH_INTERVAL, retries + 1
        )
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
        """
        current_time = int(time.time())
        results = []
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
                    if "stats" in result.keys():
                        current_ns = time.time_ns()
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (
                                current_ns - result["stats"]["publishedAt"]
                            )
                            / 1e9,
                            "execution_time": (
                                result["stats"]["executionEndedAt"]
                                - result["stats"]["executionStartedAt"]
                            ),
                            "receive_latency": (
                                result["stats"]["receivedAt"] - task_data["created_ts"]
                            )
                            / 1e9,
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
                        dataset_id=task.dataset_id,
                    )
                    asyncio.create_task(self.push([t]))
                    continue

                if self.helper.is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(
                        task, result, msg, byte_sig
                    )
                    if processed_result is None:
                        logger.debug(f"Address: {address} not valid in nodes.")
                        continue

                    pipeline_id = task.pipeline_id or ""
                    if "stats" in result.keys():
                        current_ns = time.time_ns()
                        metric_log = {
                            "node_address": address,
                            "model": result["model"],
                            "publish_latency": (
                                current_ns - result["stats"]["publishedAt"]
                            )
                            / 1e9,
                            "execution_time": (
                                result["stats"]["executionEndedAt"]
                                - result["stats"]["executionStartedAt"]
                            ),
                            "receive_latency": (
                                result["stats"]["receivedAt"] - task_data["created_ts"]
                            )
                            / 1e9,
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
                    results.append(
                        TaskResult(
                            id=identifier,
                            step_name=task.step_name,
                            result=processed_result,
                            task_input=task.workflow["external_memory"],
                            model=result["model"],
                        )
                    )
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
        await self.ping.run()

    async def execute(self, task: Union[Task, List[Task]]) -> list[TaskResult] | None:
        """
        Execute task(s) and get results.

        Args:
            task: Task(s) to execute

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
                tasks_[i : i + SCORING_BATCH_SIZE]
                for i in range(0, len(tasks_), SCORING_BATCH_SIZE)
            ]
            results = []
            for batch_tasks in batched_tasks:
                success = await self.push(batch_tasks)
                if success is False:
                    return None

                outputs = await self.fetch(task_ids=[t.id for t in batch_tasks])
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
