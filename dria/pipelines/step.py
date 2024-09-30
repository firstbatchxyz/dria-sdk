import asyncio
import json
from typing import List, Callable, Optional, Union, Dict, Any
from abc import ABC

from dria.utils.logging import logger
from dria.pipelines.config import StepConfig
from dria.client import Dria
from dria.db.storage import Storage
from dria.models import Task, CallbackType, TaskInput, TaskResult


class Step(ABC):
    """
    An abstract base class representing a step in a pipeline.

    This class encapsulates the logic for executing a single step within a larger pipeline,
    including input processing, workflow execution, and task management.

    Attributes:
        name (str): The name of the step.
        input (Union[TaskInput, List[TaskInput]]): The input(s) for this step.
        workflow (Callable): The function to be executed for this step.
        config (StepConfig): Configuration settings for this step.
        client (Optional[Dria]): The Dria instance for API interactions.
        pipeline_id (Optional[str]): The ID of the pipeline this step belongs to.
        storage (Optional[Storage]): The storage instance for persisting data.
        all_inputs (List[TaskInput]): A list of all inputs processed by this step.
        output (List[TaskResult]): The output(s) of this step.
        callback (Optional[Callable]): An optional callback function.
        callback_type (Optional[CallbackType]): The type of the callback.
        next_step_input (Optional[Any]): Input for the next step in the pipeline.
        input_keys (Optional[List[str]]): Expected keys for the input data.
        callback_params (Dict): Additional parameters for the callback function.
    """

    def __init__(
            self,
            name: str,
            input: Optional[Union[TaskInput, List[TaskInput]]] = None,
            workflow: Callable = None,
            config: StepConfig = StepConfig(),
            client: Optional[Dria] = None
    ):
        self.logger = logger
        self.name = name
        self.input = input or []
        self.workflow = workflow
        self.config = config
        self.client = client
        self.pipeline_id: Optional[str] = None
        self.storage: Optional[Storage] = None
        self.all_inputs: List[TaskInput] = []
        self.output: List[TaskResult] = []
        self.callback: Optional[Callable] = None
        self.callback_type: Optional[CallbackType] = None
        self.next_step_input: Optional[Any] = None
        self.input_keys: Optional[List[str]] = None
        self.callback_params: Dict = {}

    async def run(self) -> List[str]:
        """
        Execute the workflow for each input and push tasks to the Dria.

        Returns:
            List[str]: List of task IDs pushed to Dria.

        Raises:
            RuntimeError: If pushing any task fails.
        """
        if isinstance(self.input, TaskInput):
            self.input = [self.input]

        self.all_inputs.extend(self.input)
        task_ids = []
        try:
            for task_input in self.input:
                workflow_data = self._validate_and_run_workflow(task_input)
                task = await self._push_task(workflow_data)
                task_ids.append(task.id)
            return task_ids
        except Exception as e:
            self.logger.error(f"Error executing step '{self.name}': {e}", exc_info=True)
            raise RuntimeError(f"Failed to execute step '{self.name}': {e}") from e

    def add_pipeline_params(self, pipeline_id: str, storage: Storage, client: Dria) -> None:
        """
        Assign pipeline parameters to the step.

        Args:
            pipeline_id (str): The ID of the pipeline.
            storage (Storage): The storage instance for data persistence.
            client (Dria): The Dria instance for API interactions.
        """
        self.pipeline_id = pipeline_id
        self.storage = storage
        self.client = client
        self.logger.debug(f"Pipeline parameters added to step '{self.name}': pipeline_id={pipeline_id}")

    async def _push_task(self, workflow_data: Dict) -> Task:
        """
        Push the workflow data as a task to the Dria.

        Args:
            workflow_data (Dict): The workflow result to be pushed.

        Returns:
            Task: The task that was successfully pushed.

        Raises:
            RuntimeError: If pushing the task fails or if client/storage is not initialized.
        """
        if not self.client:
            raise RuntimeError(f"Dria is not initialized for step '{self.name}'.")

        task = Task(
            workflow=workflow_data,
            models=[model.value for model in self.config.models],
            step_name=self.name,
            pipeline_id=self.pipeline_id
        )

        success = await self.client.push(task)
        if not success:
            raise RuntimeError(f"Failed to push task for step '{self.name}'.")

        if not self.storage:
            raise RuntimeError(f"Storage is not initialized for step '{self.name}'.")

        self.storage.set_value(task.id, json.dumps(task.dict(), ensure_ascii=False))
        self.logger.debug(f"Task pushed and stored for step '{self.name}': task_id={task.id}")
        return task

    def _validate_and_run_workflow(self, task_input: TaskInput) -> Dict:
        """
        Validate the input and execute the workflow.

        Args:
            task_input (TaskInput): The input for the workflow.

        Returns:
            Dict: The result of the workflow execution.

        Raises:
            ValueError: If input keys do not match or workflow execution fails.
        """
        input_dict = task_input.dict()

        if self.input_keys and sorted(input_dict.keys()) != sorted(self.input_keys):
            error_msg = (
                f"Workflow input keys mismatch for step '{self.name}'. "
                f"Expected: {self.input_keys}, Got: {list(input_dict.keys())}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            workflow_result = self.workflow(
                input_dict,
                max_tokens=self.config.max_tokens,
                max_time=self.config.max_time,
                max_steps=self.config.max_steps
            )
            result = workflow_result.model_dump(warnings=False)
            self.logger.debug(f"Workflow executed successfully for step '{self.name}': {result}")
            return result
        except Exception as e:
            self.logger.error(f"Workflow execution failed for step '{self.name}': {e}", exc_info=True)
            raise ValueError(f"Workflow execution failed for step '{self.name}': {e}") from e
