import asyncio
import json
import traceback
import uuid
from typing import List, Optional, Dict, Any, Tuple, Union

from dria.client import Dria
from dria.constants import SCORING_BATCH_SIZE, MONITORING_INTERVAL, TASK_TIMEOUT
from dria.db.storage import Storage
from dria.models import TaskInput
from dria.models.enums import PipelineStatus
from dria.pipelines.step import Step
from dria.utils import logger


class Pipeline:
    """
    Manages a sequence of steps for processing data in a pipelines.

    Attributes:
        pipeline_id (str): Unique identifier for the pipelines.
        steps (List[Step]): Ordered list of Step objects in the pipelines.
        logger: Logger for the pipelines.
        storage (Storage): Storage object for persisting data.
        output (Dict[str, Any]): The final output of the pipelines.
        proceed_steps (List[str]): List of steps that are ready to proceed.
        client (Dria): Client for interacting with the Dria system.
    """

    def __init__(self, client: Dria):
        self.pipeline_id: str = str(uuid.uuid4())
        self.steps: List[Step] = []
        self.proceed_steps: List[str] = []
        self.output: Dict[str, Any] = {}
        self.logger = logger
        self.storage = client.storage
        self.client = client

    def add_step(self, step: Step) -> None:
        """Add a step to the pipelines."""
        step.add_pipeline_params(self.pipeline_id, self.storage, self.client)
        self.steps.append(step)
        self.logger.info(f"Added step: {step.name}")

    def get_step(self, name: str) -> Optional[Step]:
        """Get a step from the pipelines by name."""
        return next((step for step in self.steps if step.name == name), None)

    async def execute(self, return_output: bool = True) -> Union[str, Dict[str, Any]]:
        """
        Execute the entire pipeline and return the pipeline ID or output.

        Args:
            return_output (bool): If True, wait for the pipeline to complete and return the output.
                                  If False, return the pipeline ID immediately.

        Returns:
            Union[str, Dict[str, Any]]: The unique identifier of the executed pipeline if return_output is False,
                                        or the pipeline output if return_output is True.

        Raises:
            ValueError: If the pipeline has no steps.
        """
        if not self.steps:
            raise ValueError("Pipeline has no steps.")

        first_step = self.steps[0]
        await self._update_state(first_step.name)
        await self._update_status(PipelineStatus.RUNNING)
        self.logger.info(
            f"Executing pipeline '{self.pipeline_id}' starting with step '{first_step.name}'."
        )

        await self.run(first_step.name)
        asyncio.create_task(self._poll())

        if return_output:
            while True:
                _, status, output = await self.poll()
                if status == PipelineStatus.COMPLETED.value:
                    await self._graceful_shutdown()
                    return output
                await asyncio.sleep(5)
        else:
            return self.pipeline_id

    async def run(self, step_name: str) -> None:
        """
        Run a specific step in the pipelines.

        Args:
            step_name (str): The name of the step to run.

        Raises:
            ValueError: If the specified step is not found.
        """
        step = self.get_step(step_name)
        if not step:
            raise ValueError(f"Step '{step_name}' not found in the pipelines.")

        if isinstance(step.input, TaskInput):
            step.input = [step.input]

        self.logger.info(f"Running step: {step.name}")
        try:
            asyncio.create_task(step.run())
            self.logger.info(f"Step '{step.name}' completed successfully.")
        except Exception as e:
            self.logger.error(f"Error in step '{step.name}': {e}", exc_info=True)
            raise

    async def _run_next_step(self, current_step: Step, next_step_index: int) -> None:
        """Run the next step in the pipelines."""
        if next_step_index >= len(self.steps):
            self.logger.info("No more steps to execute.")
            return

        next_step = self.steps[next_step_index]
        retried_tasks = await self.client.get_retried_tasks(list(current_step.input_params.keys()))
        for i,v in retried_tasks.items():
            if i != v and v is not None:
                current_step.input_params[v] = current_step.input_params[i]
                del current_step.input_params[i]
        input_data = current_step.callback(current_step)
        if not input_data:
            raise ValueError(
                f"Step '{current_step.name}' requires at least one input to execute. Please provide input when initializing the step."
            )
        await self._update_state(next_step.name)

        next_step.input = (
            [input_data] if isinstance(input_data, TaskInput) else input_data
        )
        self.logger.info(f"Executing next step: {next_step.name}")
        await self.run(next_step.name)

    async def _poll(self) -> None:
        """Poll for results and process them."""
        try:
            current_step_index = 0
            step_round = 0
            while current_step_index < len(self.steps):
                step = self.steps[current_step_index]
                try:
                    # Check and initialize client if needed
                    if (
                        self.client.background_tasks is None
                        or self.client.background_tasks.done()
                    ):
                        if self.client.api_mode:
                            logger.debug("Background tasks closed. Reinitializing..")
                            await self.client.initialize()
                        else:
                            raise Exception("Dria client is not initialized")

                    # Calculate timeout based on input size
                    step_timeout = len(step.tasks) * TASK_TIMEOUT

                    # Process tasks in batches
                    batched_tasks = step.tasks
                    results = []
                    if not batched_tasks:
                        await asyncio.sleep(5)
                        continue

                    step_results = await self.client.fetch(
                        task=batched_tasks, timeout=step_timeout
                    )
                    if not step_results:
                        error_msg = (
                            f"Failed to fetch results for step '{step.name}'. "
                            f"Current timeout: {step_timeout}. "
                            f"Consider either:\n"
                            f"1. Using a faster model for this step\n"
                            f"2. Reducing the batch size of inputs"
                        )
                        raise ValueError(error_msg)
                    results.extend(step_results)

                    # Store results
                    for result in results:
                        step.output.append(result)

                    if ((step_round + 1) * SCORING_BATCH_SIZE) < len(step.input):
                        step_round += 1
                        await step.run(step_round)
                        continue

                    step_round = 0
                    # Handle final step
                    if self._is_final_step(step):
                        await self._finalize_pipeline(step)
                        return

                    # Move to next step
                    await self._run_next_step(step, current_step_index + 1)
                    current_step_index += 1

                except Exception as e:
                    return await self._graceful_shutdown(e)

                await asyncio.sleep(MONITORING_INTERVAL)

        finally:
            await self._graceful_shutdown()

    def _is_final_step(self, step: Step) -> bool:
        """Check if the step is the final step in the pipelines."""
        return step == self.steps[-1]

    async def _finalize_pipeline(self, final_step: Step) -> None:
        """Finalize the pipelines execution."""
        self.output = final_step.callback(final_step)
        await self._save_output()
        self.logger.info("Pipeline execution completed.")

    async def _update_state(self, state: str) -> None:
        """Update the pipelines state in storage."""
        await self.storage.set_value(f"{self.pipeline_id}_state", state)

    async def _update_status(self, status: PipelineStatus) -> None:
        """Update the pipelines status in storage."""
        await self.storage.set_value(f"{self.pipeline_id}_status", status.value)

    async def _update_error_reason(self, e: Exception) -> None:
        """Update the pipelines error reason in storage."""
        await self.storage.set_value(f"{self.pipeline_id}_error_reason", e)

    async def _graceful_shutdown(self, e: Optional[Exception] = None) -> None:
        """Gracefully shutdown the pipelines."""
        if e:
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            self.logger.info(
                f"Pipeline error details:\nType: {error_type}\nMessage: {error_message}\nTraceback:\n{error_traceback}"
            )
        await self._update_status(PipelineStatus.FAILED)
        await self._update_state(PipelineStatus.FAILED.value)
        if e:
            await self._update_error_reason(e)

        latest_step = self.steps[-1] if self.steps else None
        if latest_step:
            await self._finalize_pipeline(latest_step)
        else:
            self.logger.warning("No steps were executed before shutdown")
        await self.client.run_cleanup()

    async def _save_output(self, output: Optional[Union[str, Dict]] = None) -> None:
        """Save the pipelines output to storage."""
        try:
            if output:
                self.output = output
            if isinstance(self.output, TaskInput):
                output_data = json.dumps(self.output.dict())
            elif isinstance(self.output, list) and isinstance(
                self.output[0], TaskInput
            ):
                output_data = json.dumps([i.dict() for i in self.output])
            else:
                output_data = json.dumps(self.output)
        except IndexError as e:
            output_data = []
        await self.storage.set_value(f"{self.pipeline_id}_output", output_data)
        await self._update_status(PipelineStatus.COMPLETED)

    async def poll(self) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """
        Poll for pipelines results.

        Returns:
            Tuple[str, str, Optional[Dict[str, Any]]]: Pipeline state, status, and output (if completed).

        Raises:
            ValueError: If the pipelines is not found.
        """
        output = await self.storage.get_value(f"{self.pipeline_id}_output")
        status = await self.storage.get_value(f"{self.pipeline_id}_status")
        state = await self.storage.get_value(f"{self.pipeline_id}_state")

        if status == PipelineStatus.FAILED.value:
            error_reason = await self.storage.get_value(
                f"{self.pipeline_id}_error_reason"
            )
            raise Exception(f"Pipeline execution failed: {error_reason}")

        if not status or not state:
            raise ValueError("Pipeline not found")

        return state, status, json.loads(output) if output else None
