import asyncio
import json
import time
import uuid
from typing import List, Optional, Dict, Any, Tuple, Union

from dria.client import Dria
from dria.db.storage import Storage
from dria.models import TaskResult, TaskInput
from dria.models.enums import PipelineStatus
from dria.pipelines.config import PipelineConfig
from dria.pipelines.step import Step
from dria.utils import logger


class Pipeline:
    """
    Manages a sequence of steps for processing data in a pipeline.

    Attributes:
        pipeline_id (str): Unique identifier for the pipeline.
        steps (List[Step]): Ordered list of Step objects in the pipeline.
        logger: Logger for the pipeline.
        storage (Storage): Storage object for persisting data.
        config (PipelineConfig): Configuration for the pipeline.
        output (Dict[str, Any]): The final output of the pipeline.
        proceed_steps (List[str]): List of steps that are ready to proceed.
        client (Dria): Client for interacting with the Dria system.
    """

    def __init__(self, client: Dria, config: PipelineConfig):
        self.pipeline_id: str = str(uuid.uuid4())
        self.steps: List[Step] = []
        self.proceed_steps: List[str] = []
        self.output: Dict[str, Any] = {}
        self.logger = logger
        self.storage = client.storage
        self.client = client
        self.config = config

    def add_step(self, step: Step) -> None:
        """Add a step to the pipeline."""
        step.add_pipeline_params(self.pipeline_id, self.storage, self.client)
        self.steps.append(step)
        self.logger.info(f"Added step: {step.name}")

    def get_step(self, name: str) -> Optional[Step]:
        """Get a step from the pipeline by name."""
        return next((step for step in self.steps if step.name == name), None)

    async def execute(self) -> str:
        """
        Execute the entire pipeline and return the pipeline ID.

        Returns:
            str: The unique identifier of the executed pipeline.

        Raises:
            ValueError: If the pipeline has no steps.
        """
        if not self.steps:
            raise ValueError("Pipeline has no steps.")

        first_step = self.steps[0]
        self._update_state(first_step.name)
        self._update_status(PipelineStatus.RUNNING)
        self.logger.info(f"Executing pipeline '{self.pipeline_id}' starting with step '{first_step.name}'.")

        await self.run(first_step.name)
        asyncio.create_task(self._poll())

        return self.pipeline_id

    async def run(self, step_name: str) -> None:
        """
        Run a specific step in the pipeline.

        Args:
            step_name (str): The name of the step to run.

        Raises:
            ValueError: If the specified step is not found.
        """
        step = self.get_step(step_name)
        if not step:
            raise ValueError(f"Step '{step_name}' not found in the pipeline.")

        self.logger.info(f"Running step: {step.name}")
        try:
            asyncio.create_task(step.run())
            self.logger.info(f"Step '{step.name}' completed successfully.")
        except Exception as e:
            self.logger.error(f"Error in step '{step.name}': {e}", exc_info=True)
            raise

    async def _run_next_step(self, current_step: Step, next_step_index: int) -> None:
        """Run the next step in the pipeline."""
        if next_step_index >= len(self.steps):
            self.logger.info("No more steps to execute.")
            return

        next_step = self.steps[next_step_index]
        input_data = current_step.callback(current_step)
        self._update_state(next_step.name)

        next_step.input = [input_data] if isinstance(input_data, TaskInput) else input_data
        self.logger.info(f"Executing next step: {next_step.name}")
        await self.run(next_step.name)

    async def _poll(self) -> None:
        """Poll for results and process them."""
        start_time = time.time()
        while True:
            try:
                if time.time() - start_time > self.config.pipeline_timeout:
                    self._handle_deadline_exceeded()
                    return

                results: List[TaskResult] = await self.client.fetch(pipeline=self)
                for result in results:
                    step = self.get_step(result.step_name)
                    if not step:
                        self.logger.warning(f"Received result for unknown step '{result.step_name}'.")
                        continue

                    step.output.append(result)
                    if not self._check_step_requirements(step):
                        continue
                    if self._is_final_step(step):
                        self._finalize_pipeline(step)
                        return

                    await self._run_next_step(step, self.steps.index(step) + 1)

            except Exception as e:
                self._update_status(PipelineStatus.FAILED)
                self._update_state(PipelineStatus.FAILED.value)
                raise Exception({"error": "Error polling results", "exception": e})

            await asyncio.sleep(self.config.retry_interval)

    def _check_step_requirements(self, step: Step) -> bool:
        """Check if the step requirements are met."""
        if len(step.all_inputs) == 1:
            self.proceed_steps.append(step.name)
            return True
        required_results = int(len(step.all_inputs) * step.config.min_compute)
        self.logger.info(f"Required Output: {required_results}, processed output: {len(step.output)}")
        if len(step.output) < int(required_results) or step.name in self.proceed_steps:
            return False
        self.proceed_steps.append(step.name)
        return True

    def _is_final_step(self, step: Step) -> bool:
        """Check if the step is the final step in the pipeline."""
        return step == self.steps[-1]

    def _finalize_pipeline(self, final_step: Step) -> None:
        """Finalize the pipeline execution."""
        self.output = final_step.callback(final_step)
        self._save_output()
        self.logger.info("Pipeline execution completed successfully.")

    def _handle_deadline_exceeded(self) -> None:
        """Handle the deadline exceeded error."""
        self.logger.error(f"Pipeline '{self.pipeline_id}' exceeded the deadline of {self.config.pipeline_timeout} seconds.")
        self._update_status(PipelineStatus.FAILED)
        self._update_state(PipelineStatus.FAILED.value)
        self.logger.warning(f"Terminating pipeline execution due to deadline exceeded. Current pipeline deadline {self.config.pipeline_timeout}")

    def _update_state(self, state: str) -> None:
        """Update the pipeline state in storage."""
        self.storage.set_value(f"{self.pipeline_id}_state", state)

    def _update_status(self, status: PipelineStatus) -> None:
        """Update the pipeline status in storage."""
        self.storage.set_value(f"{self.pipeline_id}_status", status.value)

    def _save_output(self, output: Optional[Union[str, Dict]] = None) -> None:
        """Save the pipeline output to storage."""
        if output:
            self.output = output
        if isinstance(self.output, TaskInput):
            output_data = json.dumps(self.output.dict())
        elif isinstance(self.output, list) and isinstance(self.output[0], TaskInput):
            output_data = json.dumps([i.dict() for i in self.output])
        else:
            output_data = json.dumps(self.output)
        self.storage.set_value(f"{self.pipeline_id}_output", output_data)
        self._update_status(PipelineStatus.COMPLETED)

    def poll(self) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """
        Poll for pipeline results.

        Returns:
            Tuple[str, str, Optional[Dict[str, Any]]]: Pipeline state, status, and output (if completed).

        Raises:
            ValueError: If the pipeline is not found.
        """
        output = self.storage.get_value(f"{self.pipeline_id}_output")
        status = self.storage.get_value(f"{self.pipeline_id}_status")
        state = self.storage.get_value(f"{self.pipeline_id}_state")

        if not status or not state:
            raise ValueError("Pipeline not found")

        return state, status, json.loads(output) if output else None
