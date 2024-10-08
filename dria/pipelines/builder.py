import inspect
from types import SimpleNamespace
from typing import Dict, List, Callable, Optional, Union, Any, get_type_hints
import uuid

from dria_workflows import Workflow

from dria.client import Dria
from dria.models import TaskInput, CallbackType, Model
from dria.pipelines.config import StepConfig, PipelineConfig
from dria.pipelines.pipeline import Pipeline
from dria.pipelines.step import Step
from dria.pipelines.callbacks import (
    aggregation_callback,
    broadcast_callback,
    default_callback,
    scatter_callback,
)
from dria.utils.logging import logger
import random
import string
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel, create_model, ValidationError


class StepType(str, Enum):
    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"


class StepTemplate(BaseModel, ABC):
    step_type: StepType = StepType.FIRST
    workflow: Optional[Workflow] = None
    params: SimpleNamespace = SimpleNamespace()
    config: StepConfig = StepConfig()

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, config: Optional[StepConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self._map_io(**kwargs)
        if config:
            self.config = config

    def get_params(self) -> dict:
        return vars(self.params)

    def _generate_dummy_inputs(self, func: Callable) -> Dict[str, Any]:
        dummy_inputs = {}
        type_hints = get_type_hints(func)
        signature = inspect.signature(func)

        for param_name, _ in signature.parameters.items():
            if param_name in ["self", "kwargs"]:
                continue
            param_type = type_hints.get(param_name, Any)
            dummy_inputs[param_name] = self._create_dummy_data(param_type)

        return dummy_inputs

    def _create_dummy_data(self, param_type):
        if param_type == str:
            return "".join(random.choices(string.ascii_letters, k=10))
        elif param_type == int:
            return random.randint(0, 100)
        elif param_type == float:
            return random.uniform(0, 100)
        elif param_type == bool:
            return random.choice([True, False])
        elif param_type == List[str]:
            return [
                "".join(random.choices(string.ascii_letters, k=5)) for _ in range(3)
            ]
        elif param_type == List[int]:
            return [random.randint(0, 100) for _ in range(3)]
        elif param_type == Dict[str, Any]:
            return {f"key_{i}": self._create_dummy_data(str) for i in range(3)}
        else:
            return None

    def _map_io(self, **kwargs):

        for k, v in kwargs.items():
            setattr(self.params, k, v)

        self.params.inputs = []
        workflow_inputs = self._generate_dummy_inputs(self.create_workflow)
        task_input = TaskInput(**workflow_inputs)
        self.params.task_input = task_input
        for k, v in workflow_inputs.items():
            self.params.inputs.append(k)

        self.workflow = self.create_workflow(**workflow_inputs)

        if not self.workflow.return_value:
            raise ValueError("Workflow must have a return value.")

        self.params.output = self.workflow.return_value.input.key
        self.params.output_type = self.workflow.return_value.input.type
        self.params.output_json = self.workflow.return_value.to_json
        self.params.callback = self.callback
        self.params.callback_type = CallbackType.DEFAULT

    def broadcast(self, n: int) -> "StepTemplate":
        """

        Args:
            n: broadcast to N nodes

        Returns:

        """
        self.params.callback = broadcast_callback
        self.params.callback_params = {"n": n}
        self.params.callback_type = CallbackType.BROADCAST
        return self

    def scatter(self) -> "StepTemplate":
        """
        Scatter N outputs to N nodes
        Returns:

        """
        self.params.callback = scatter_callback
        self.params.callback_type = CallbackType.SCATTER
        return self

    def aggregate(self) -> "StepTemplate":
        """
        Aggregate N outputs to 1 node
        Returns:

        """
        self.params.callback = aggregation_callback
        self.params.callback_type = CallbackType.AGGREGATE
        return self

    def custom(self) -> "StepTemplate":
        """
        Custom callback
        Returns:

        """
        self.params.callback = self.callback
        self.params.callback_type = CallbackType.CUSTOM
        return self

    @abstractmethod
    def create_workflow(self, **kwargs) -> "Workflow":
        pass

    def set_models(self, models: Optional[List[Model]] = None) -> "StepTemplate":
        if models:
            self.config.models = models
        return self

    def set_workflow_params(
        self,
        min_compute: Optional[int] = None,
        max_time: Optional[int] = None,
        max_steps: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> "StepTemplate":
        if min_compute:
            self.config.min_compute = min_compute
        if max_time:
            self.config.max_time = max_time
        if max_steps:
            self.config.max_steps = max_steps
        if max_tokens:
            self.config.max_tokens = max_tokens
        return self

    def callback(self, step: "Step") -> Union[List[TaskInput], TaskInput]:
        if self.__class__.callback is not StepTemplate.callback:
            return self.__class__.callback(self, step)
        return default_callback(step)

    @staticmethod
    def parse(result) -> Any:
        pass


class StepBuilder:
    """
    A builder class for creating and configuring pipelines steps.

    This class provides a fluent interface for step creation and configuration,
    allowing for easy setup of step properties such as callbacks and configurations.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        input: Optional[Union[TaskInput, List[TaskInput]]] = None,
        workflow: Optional[Union[Callable, Workflow]] = None,
        config: StepConfig = StepConfig(),
    ):
        """
        Initialize a new StepBuilder instance.

        Args:
            name (Optional[str]): The name of the step. If not provided, a UUID will be generated.
            input (Optional[Union[TaskInput, List[TaskInput]]]): The input(s) for the step.
            workflow (Optional[Callable]): The workflow function for the step.
            config (StepConfig): The configuration for the step. Defaults to an empty StepConfig.
        """
        self.step = Step(
            name=name or str(uuid.uuid4()),
            input=input,
            workflow=workflow,
            config=config,
        )
        logger.debug(f"Created StepBuilder with name: {self.step.name}")

    def add_callback(
        self,
        callback: Callable,
        callback_type: CallbackType,
        params: Optional[Dict] = None,
    ) -> "StepBuilder":
        """
        Set a custom callback for the step.

        Args:
            callback (Callable): Custom callback function.
            callback_type (CallbackType): Type of the custom callback.
            params (Optional[Dict]): Extra parameters for the custom callback.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        if not callable(callback):
            raise ValueError("Custom callback must be callable")

        if not any(
            param.annotation in [Step, "Step"]
            for param in inspect.signature(callback).parameters.values()
        ):
            raise ValueError("Custom callback must have a parameter of type Step")

        self.step.callback = callback
        self.step.callback_type = callback_type
        self.step.callback_params = params or {}
        logger.debug(f"Set custom callback for step: {self.step.name}")
        return self

    def set_config(self, config: StepConfig) -> "StepBuilder":
        """
        Set the configuration for the step.

        Args:
            config (StepConfig): The configuration for the step.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        self.step.config = config
        logger.debug(f"Set config for step: {self.step.name}")
        return self

    def build(self) -> Step:
        """
        Build and return the configured Step instance.

        Returns:
            Step: The fully configured Step instance.
        """
        if not self.step.config:
            self.step.config = StepConfig()

        if self.step.callback is None:
            self.step.callback = default_callback
            self.step.callback_type = CallbackType.DEFAULT

        logger.info(f"Built step: {self.step.name}")
        return self.step


class PipelineBuilder:
    """
    A builder class for creating and configuring pipelines.

    This class provides methods to add steps to a pipelines and build the final Pipeline instance.
    """

    def __init__(self, config: PipelineConfig, dria_client: Dria):
        """
        Initialize a new PipelineBuilder instance.

        Args:
            config (PipelineConfig): The configuration for the pipelines.
            dria_client (Dria): The Dria client instance.
        """
        self.steps: List[Step] = []
        self.templates: List[StepTemplate] = []
        self.config = config
        self.dria_client = dria_client
        self.pipeline_input: Optional[Dict] = None
        logger.info("Initialized PipelineBuilder")

    def _check_unique_step_names(self):
        """
        Check if all step names in the pipelines are unique.

        Raises:
            ValueError: If duplicate step names are found.
        """
        step_names = set()
        for step in self.steps:
            if step.name in step_names:
                raise ValueError(
                    f"Duplicate step name found: {step.name}. Each step must have a unique name."
                )
            step_names.add(step.name)

    def input(self, **kwargs):
        self.pipeline_input = kwargs
        return self

    def _validate_input_types(self, step_template: StepTemplate):
        if not self.pipeline_input:
            raise ValueError(
                "Pipeline input not set. Use .input() method before adding steps."
            )

        expected_types = get_type_hints(step_template.create_workflow)
        input_model = create_model(
            "InputModel",
            **{k: (v, ...) for k, v in expected_types.items() if k != "return"},
        )

        try:
            input_model(**self.pipeline_input)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                if error["type"] == "value_error.missing":
                    error_messages.append(f"Missing input field: {error['loc'][0]}")
                else:
                    error_messages.append(
                        f"Invalid input for field '{error['loc'][0]}': {error['msg']}"
                    )
            raise ValueError("\n".join(error_messages))

    def _add_step(self, step: Step) -> "PipelineBuilder":
        """
        Add a step to the pipelines.

        Args:
            step (Step): Step to add to the pipelines.

        Returns:
            PipelineBuilder: Self instance for method chaining.

        Raises:
            ValueError: If the step configuration is invalid.
        """
        try:
            # Check if step.workflow is callable
            if not callable(step.workflow):
                workflow = step.workflow
            else:
                workflow = step.workflow({})
            step_inputs = [p.name for task in workflow.tasks for p in task.inputs]
            step_outputs = [p.key for task in workflow.tasks for p in task.outputs]
            previous_step = self.steps[-1] if self.steps else None
            step.input_keys = list(
                set([key for key in step_inputs if key not in step_outputs])
            )
            if previous_step:
                previous_step.next_step_input = step.input_keys

            if step.callback_type in (
                CallbackType.BROADCAST,
                CallbackType.AGGREGATE,
                CallbackType.SCATTER,
            ):
                if len(step.input_keys) > 1:
                    raise ValueError(
                        "Broadcast and Aggregate callbacks only support a single input for this step. "
                        "If you want to use multiple inputs, use a custom callback."
                    )

            self.steps.append(step)
        except Exception as e:
            logger.error(f"Error adding step {step.name}: {str(e)}")
            raise
        return self

    def __lshift__(self, other: StepTemplate):
        """
        Add a step to the pipelines using the given StepTemplate.
        Args:
            other:

        Returns:

        """
        task_input = None
        if len(self.steps) == 0:
            self._validate_input_types(other)
            task_input = TaskInput(**self.pipeline_input)

        _step = StepBuilder(
            name=other.__class__.__name__ + f".{len(self.steps)}",
            config=other.config,
            input=task_input,
            workflow=other.workflow,
        ).add_callback(other.params.callback, other.params.callback_type)

        self._add_step(_step.build())
        self.templates.append(other)
        return self

    def build(self) -> Pipeline:
        """
        Build and return the configured Pipeline instance.

        Returns:
            Pipeline: The fully configured Pipeline instance.

        Raises:
            Exception: If there's an error during pipelines building.
        """
        try:
            pipeline = Pipeline(client=self.dria_client, config=self.config)

            self._check_unique_step_names()
            # Note: Uncomment the following line if you want to enforce no callback on the last step
            # self._check_last_step_callback()

            for step in self.steps:
                pipeline.add_step(step)
            logger.info("Built pipelines successfully")
            return pipeline
        except Exception as e:
            logger.error(f"Error building pipelines: {str(e)}")
            raise
