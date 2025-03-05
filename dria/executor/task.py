import asyncio
import base64
import json
import signal
import time
from typing import Any, List, Dict, Union, Optional, Tuple

from Crypto.Hash import keccak

# Internal imports from other modules
from dria.constants import (
    FETCH_INTERVAL,
    SCORING_BATCH_SIZE,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models.exceptions import TaskPublishError
from dria.request import RPCClient
from dria.utilities.helper import Helper
from dria.utilities.logging.logging import logger
from dria.utilities import evaluate_nodes
from dria.utilities.crypto import (
    get_truthful_nodes,
    generate_task_keys,
    recover_public_key,
    uncompressed_public_key,
)

# Local imports
from .ping import Ping

# Import TaskManager directly to avoid circular dependency
from dria.manager import TaskManager
from .. import TaskResult, Task


class TaskExecutor:
    """
    Executor for distributed task processing across the network.

    Handles task submission, result fetching, and processing of responses
    from network nodes. Includes retry logic and validation of results.
    """

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
        """
        Initialize the TaskExecutor.

        Args:
            ping: Ping instance for network heartbeat monitoring
            rpc: RPCClient for network communication
            storage: Storage instance for persisting data
            kv: KeyValueQueue for message queuing
            task_manager: TaskManager for task distribution
        """
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
        """
        Handle termination signals by initiating graceful shutdown.

        Args:x
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        asyncio.create_task(self._set_shutdown())

    async def _set_shutdown(self) -> None:
        """Set shutdown event asynchronously."""
        self.shutdown_event.set()

    async def push(self, tasks: List[Task]) -> bool:
        """
        Submit tasks to the network.

        Args:
            tasks: List of tasks to submit
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
                if attempts > 0 and attempts % 20 == 0:
                    logger.info("Waiting for nodes to be available...")
                await self.check_heartbeat()
                nodes, filters, models = await self.task_manager.create_filter(
                    tasks, self.stats
                )
                attempts += 1

            selected_models = []
            for idx, (node, filter_data, model) in enumerate(
                zip(nodes, filters, models)
            ):
                tasks[idx].nodes = [node]
                tasks[idx].filter = filter_data
                selected_models.append(model)

            await asyncio.gather(
                *[
                    self.task_manager.push_task(task, selected_models[idx])
                    for idx, task in enumerate(tasks)
                ]
            )
            logger.debug("Tasks successfully published")
            return True

        except Exception as e:
            raise TaskPublishError(f"Failed to publish task: {e}") from e

    async def fetch(
        self,
        task_ids: List[str],
        fetch_interval: int = FETCH_INTERVAL,
    ) -> List[TaskResult]:
        """
        Fetch and process task results with iterative retry logic.

        Args:
            task_ids: Execution id to fetch results for
            fetch_interval: Initial interval between fetch attempts in seconds

        Returns:
            List of processed task results
        """
        all_results = []
        remaining_task_ids = task_ids.copy()
        retries = 0
        current_interval = fetch_interval

        while remaining_task_ids and retries <= self.MAX_RETRIES_FOR_AVAILABILITY:
            results, failed_tasks = await self.poll(remaining_task_ids)
            if failed_tasks:
                logger.debug("Failed tasks are retrying...")

            if results:
                all_results.extend(results)
                # Remove successfully fetched tasks from remaining list
                result_ids = {r.id for r in results}
                remaining_task_ids = [
                    t for t in remaining_task_ids if t not in result_ids
                ]
                # Reset interval on successful fetch
                current_interval = min(current_interval * 2, 30)
            else:
                retries += 1
                # Exponential backoff with maximum cap
                current_interval = min(current_interval * 2, 30)

            if remaining_task_ids and retries <= self.MAX_RETRIES_FOR_AVAILABILITY:
                await asyncio.sleep(current_interval)

        return all_results

    async def poll(
        self, task_ids: List[str]
    ) -> Tuple[Optional[List[TaskResult]], Optional[List[Task]]]:
        """
        Poll output content topic for task results.

        Args:
            task_ids: List of task IDs to poll for

        Returns:
            List of task results or None if polling failed, List of failed tasks

        Raises:
            Exception: If error occurs during polling
        """
        try:
            topic_results = await self.rpc.get_results(task_ids)
            if topic_results:
                return await self._process_results(list(set(topic_results)))
            return [], []
        except Exception as e:
            raise Exception(f"Error fetching content topic: {e}")

    async def _process_results(
        self, topic_results: List[str]
    ) -> Tuple[List[TaskResult], List[Task]]:
        """
        Process raw results from output content topic.

        Args:
            topic_results: Raw results from topic

        Returns:
            List of processed TaskResult objects, List of failed tasks
        """
        current_time = int(time.time())
        results = []
        failed_tasks = []

        for item in topic_results:
            try:
                # Parse the raw output message
                output = json.loads(item)

                # Extract message and signature components
                message = output["message"]
                signature = bytes.fromhex(output["signature"])

                # Append recovery ID to signature for verification
                complete_signature = signature + output["recovery_id"].to_bytes(
                    1, byteorder="big"
                )

                # Decode and parse the base64-encoded message content
                decoded_content = json.loads(base64.b64decode(message).decode("utf-8"))

                # Extract task identifier and RPC authentication token
                task_identifier, rpc_auth = decoded_content["taskId"].split("--")
                task_data = await self.storage.get_value(task_identifier)
                if not task_data:
                    logger.debug(
                        f"Task data not found for identifier: {task_identifier}"
                    )
                    continue

                task_data = json.loads(task_data)
                if "new_task_id" in task_data:
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
                await self.storage.set_value(
                    task_identifier, json.dumps(task.model_dump())
                )

                # Handle error case
                if "error" in decoded_content:
                    public_key = recover_public_key(
                        complete_signature, message.encode()
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
                        error_msg = decoded_content["error"].split(
                            "Workflow execution failed: "
                        )[1]
                    except IndexError:
                        error_msg = decoded_content["error"]
                    logger.debug(f"ID: {task_identifier} {error_msg}. Task retrying..")

                    # Log metrics for failed task
                    if "stats" in decoded_content:
                        self._log_metrics(decoded_content, task_data, address, True)

                    # Handle prompt errors specially
                    if "Invalid prompt" in decoded_content["error"]:
                        logger.error(f"{decoded_content['error']}")
                        results.append(
                            TaskResult(
                                id=task_identifier,
                                result=None,
                                inputs=task.workflow["external_memory"],
                                model=decoded_content["model"],
                                error=decoded_content["error"],
                            )
                        )
                        continue

                    # Retry the task
                    workflow = await self.storage.get_value(f"{task.id}:workflow")
                    t = Task(
                        id=task.id,
                        workflow=workflow,
                        models=task.models,
                        dataset_id=task.dataset_id,
                    )
                    failed_tasks.append(t)
                    continue

                # Process valid task result
                if self.helper.is_task_valid(task, current_time):
                    processed_result, address = get_truthful_nodes(
                        task, decoded_content, message, complete_signature
                    )
                    if processed_result is None:
                        logger.debug(f"Address: {address} not valid in nodes.")
                        continue

                    # Log metrics for successful task
                    if "stats" in decoded_content:
                        self._log_metrics(decoded_content, task_data, address)

                    # Add to results list
                    results.append(
                        TaskResult(
                            id=task_identifier,
                            result=processed_result,
                            inputs=task.workflow["external_memory"],
                            model=decoded_content["model"],
                            error=None,
                        )
                    )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error processing item: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error processing item: {e}", exc_info=True)

        return results, failed_tasks

    def _log_metrics(
        self, result: Dict, task_data: Dict, address: str, error: bool = False
    ) -> None:
        """
        Log performance metrics for a task.

        Args:
            result: Task result data
            task_data: Original task data
            address: Node address
            error: Whether the task resulted in an error
        """
        current_ns = time.time_ns()
        metric_log = {
            "node_address": address,
            "model": result["model"],
            "publish_latency": (current_ns - result["stats"]["publishedAt"]) / 1e9,
            "execution_time": (
                result["stats"]["executionEndedAt"]
                - result["stats"]["executionStartedAt"]
            ),
            "receive_latency": (result["stats"]["receivedAt"] - task_data["created_ts"])
            / 1e9,
            "roundtrip": (current_ns - task_data["created_ts"]) / 1e9,
        }

        if error:
            metric_log["error"] = True

        task_id = task_data.get("id", "unknown")
        logger.debug(f"Task id: {task_id}, Metrics: {metric_log}")
        self.metrics.append(metric_log)

    async def check_heartbeat(self) -> None:
        """
        Check if heartbeat is still valid and run ping if needed.
        """
        if not await self.task_manager.should_monitor():
            return
        await self.ping.run()

    async def execute(
        self, task: Union[Task, List[Task]]
    ) -> tuple[None, None] | tuple[list[TaskResult], list[list[Task]]]:
        """
        Execute task(s) and get results.

        Args:
            task: Single Task or list of Task objects to execute

        Returns:
            List of task results or None if execution failed

        Raises:
            ValueError: If invalid task type or empty task list
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
            # Create deep copies to avoid modifying original tasks
            tasks_ = [t.__deepcopy__() for t in tasks]

            # Split into batches for processing
            batched_tasks = [
                tasks_[i : i + SCORING_BATCH_SIZE]
                for i in range(0, len(tasks_), SCORING_BATCH_SIZE)
            ]

            results = []
            for batch_tasks in batched_tasks:
                success = await self.push(batch_tasks)
                if not success:
                    return None, None

                task_ids = [t.id for t in batch_tasks]
                outputs = await self.fetch(task_ids=task_ids)

                # Filter out None results
                valid_results = [
                    output for output in outputs if output.result is not None
                ]
                results.extend(valid_results)

                # Update node performance statistics
                self.stats = evaluate_nodes(self.metrics, self.stats)
                self.metrics = []

            return results, batched_tasks
        except Exception as e:
            logger.error(f"Error during task execution: {str(e)}")
            raise
