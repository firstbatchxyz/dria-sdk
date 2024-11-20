import json
from abc import ABC
from copy import deepcopy
from typing import List, Callable, Optional, Union, Dict, Any

from dria_workflows import Workflow

from dria.client import Dria
from dria.constants import SCORING_BATCH_SIZE
from dria.db.storage import Storage
from dria.models import Task, CallbackType, TaskInput, TaskResult
from dria.pipelines.config import StepConfig
from dria.utils.logging import logger


class Step(ABC):
    """
    An abstract base class representing a step in a pipelines.

    This class encapsulates the logic for executing a single step within a larger pipelines,
    including input processing, workflow execution, and task management.

    Attributes:
        name (str): The name of the step.
        input (Union[TaskInput, List[TaskInput]]): The input(s) for this step.
        workflow (Callable): The function to be executed for this step.
        config (StepConfig): Configuration settings for this step.
        client (Optional[Dria]): The Dria instance for API interactions.
        pipeline_id (Optional[str]): The ID of the pipelines this step belongs to.
        storage (Optional[Storage]): The storage instance for persisting data.
        output (List[TaskResult]): The output(s) of this step.
        callback (Optional[Callable]): An optional callback function.
        callback_type (Optional[CallbackType]): The type of the callback.
        next_step_input (Optional[Any]): Input for the next step in the pipelines.
        input_keys (Optional[List[str]]): Expected keys for the input data.
        callback_params (Dict): Additional parameters for the callback function.
    """

    def __init__(
        self,
        name: str,
        input: Optional[Union[TaskInput, List[TaskInput]]] = None,
        workflow: Union[Callable, Workflow] = None,
        config: StepConfig = StepConfig(),
        client: Optional[Dria] = None,
    ):
        self.logger = logger
        self.name = name
        self.input = input or []
        self.workflow = workflow
        self.config = config
        self.client = client
        self.pipeline_id: Optional[str] = None
        self.storage: Optional[Storage] = None
        self.output: List[TaskResult] = []
        self.callback: Optional[Callable] = None
        self.callback_type: Optional[CallbackType] = None
        self.next_step_input: Optional[Any] = None
        self.input_keys: Optional[List[str]] = None
        self.tasks = []
        self.callback_params: Dict = {}

    async def run(self, step_round=0):
        """
        Execute the workflow for each input and push tasks to the Dria.

        Returns:
            List[str]: List of task IDs pushed to Dria.

        Raises:
            RuntimeError: If pushing any task fails.
        """

        try:
            if isinstance(self.input, list):
                batched_input = self.input[
                    step_round
                    * SCORING_BATCH_SIZE : (step_round + 1)
                    * SCORING_BATCH_SIZE
                ]
            else:
                batched_input = [self.input]
            await self._push_task(
                [deepcopy(self._validate_and_run_workflow(i)) for i in batched_input]
            )
        except Exception as e:
            self.logger.error(f"Error executing step '{self.name}': {e}", exc_info=True)
            raise RuntimeError(f"Failed to execute step '{self.name}': {e}") from e

    def add_pipeline_params(
        self, pipeline_id: str, storage: Storage, client: Dria
    ) -> None:
        """
        Assign pipelines parameters to the step.

        Args:
            pipeline_id (str): The ID of the pipelines.
            storage (Storage): The storage instance for data persistence.
            client (Dria): The Dria instance for API interactions.
        """
        self.pipeline_id = pipeline_id
        self.storage = storage
        self.client = client
        self.logger.debug(
            f"Pipeline parameters added to step '{self.name}': pipeline_id={pipeline_id}"
        )

    async def _push_task(self, workflows: List[Workflow]):
        """
        Push the workflow data as a task to the Dria.

        Args:
            workflows (Workflow): The workflow result to be pushed.

        Returns:
            Task: The task that was successfully pushed.

        Raises:
            RuntimeError: If pushing the task fails or if client/storage is not initialized.
        """
        self.tasks = []
        if not self.client:
            raise RuntimeError(f"Dria is not initialized for step '{self.name}'.")
        tasks = [
            Task(
                workflow=w,
                models=[model.value for model in self.config.models],
                step_name=self.name,
                pipeline_id=self.pipeline_id,
            )
            for w in workflows
        ]
        success = await self.client.push(tasks)
        if not success:
            raise RuntimeError(f"Failed to push task for step '{self.name}'.")

        if not self.storage:
            raise RuntimeError(f"Storage is not initialized for step '{self.name}'.")
        for task in tasks:
            self.tasks.append(task)
            await self.storage.set_value(
                task.id, json.dumps(task.dict(), ensure_ascii=False)
            )

    def _validate_and_run_workflow(self, task_input: TaskInput) -> Workflow:
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

        if self.input_keys and not set(sorted(self.input_keys)).issubset(
            set(sorted(input_dict.keys()))
        ):
            error_msg = (
                f"Workflow input keys mismatch for step '{self.name}'. "
                f"Expected: {self.input_keys}, Got: {list(input_dict.keys())}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            if isinstance(self.workflow, Workflow):
                workflow_result = self.workflow
                workflow_result.external_memory.update(
                    {
                        key: (
                            str(input_dict[key])
                            if isinstance(input_dict[key], (int, float))
                            else (
                                [str(x) for x in input_dict[key]]
                                if isinstance(input_dict[key], list)
                                and all(
                                    isinstance(x, (int, float)) for x in input_dict[key]
                                )
                                else input_dict[key]
                            )
                        )
                        for key in self.input_keys
                        if key in input_dict
                    }
                )
            else:
                workflow_result = self.workflow(
                    input_dict,
                    max_tokens=self.config.max_tokens,
                    max_time=self.config.max_time,
                    max_steps=self.config.max_steps,
                )
            self.logger.debug(f"Workflow built successfully for step '{self.name}'")
            return workflow_result
        except Exception as e:
            self.logger.error(
                f"Workflow execution failed for step '{self.name}': {e}", exc_info=True
            )
            raise ValueError(
                f"Workflow execution failed for step '{self.name}': {e}"
            ) from e
