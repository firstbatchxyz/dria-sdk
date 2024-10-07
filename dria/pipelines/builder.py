import inspect
from types import SimpleNamespace
from typing import Dict, List, Callable, Optional, Union, Any, get_type_hints
import uuid

from dria_workflows import Workflow

from dria.client import Dria
from dria.models import TaskInput, CallbackType
from dria.pipelines.config import StepConfig, PipelineConfig
from dria.pipelines.pipeline import Pipeline
from dria.pipelines.step import Step
from dria.pipelines.callbacks import (
    aggregation_callback,
    broadcast_callback,
    default_callback,
    scatter_callback
)
from dria.utils.logging import logger
import random
import string
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel


class StepType(str, Enum):
    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"


class StepTemplate(BaseModel, ABC):
    step_type: StepType = StepType.FIRST
    workflow: Optional[Workflow] = None
    params: SimpleNamespace = SimpleNamespace()

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._map_io(**kwargs)

    def get_params(self) -> dict:
        return vars(self.params)

    def _generate_dummy_inputs(self, func: Callable) -> Dict[str, Any]:
        dummy_inputs = {}
        type_hints = get_type_hints(func)
        signature = inspect.signature(func)

        for param_name, param in signature.parameters.items():
            if param_name in ['self', 'kwargs']:
                continue
            param_type = type_hints.get(param_name, Any)
            dummy_inputs[param_name] = self._create_dummy_data(param_type)

        return dummy_inputs

    def _create_dummy_data(self, param_type):
        if param_type == str:
            return ''.join(random.choices(string.ascii_letters, k=10))
        elif param_type == int:
            return random.randint(0, 100)
        elif param_type == float:
            return random.uniform(0, 100)
        elif param_type == bool:
            return random.choice([True, False])
        elif param_type == List[str]:
            return [''.join(random.choices(string.ascii_letters, k=5)) for _ in range(3)]
        elif param_type == List[int]:
            return [random.randint(0, 100) for _ in range(3)]
        elif param_type == Dict[str, Any]:
            return {f'key_{i}': self._create_dummy_data(str) for i in range(3)}
        else:
            return None

    def _map_io(self, **kwargs):

        self.params.inputs = []
        if not kwargs or len(kwargs) == 0:
            kwargs = self._generate_dummy_inputs(self.create_workflow)

        task_input = TaskInput(**kwargs)
        self.params.task_input = task_input
        for k, v in kwargs.items():
            setattr(self.params, k, v)
            self.params.inputs.append(k)

        self.workflow = self.create_workflow(**kwargs)

        if not self.workflow.return_value:
            raise ValueError("Workflow must have a return value.")

        self.params.output = self.workflow.return_value.input.key
        self.params.output_type = self.workflow.return_value.input.type
        self.params.output_json = self.workflow.return_value.to_json

    def broadcast(self, n: int) -> 'StepTemplate':
        """

        Args:
            n: broadcast to N nodes

        Returns:

        """
        self.params.callback = broadcast_callback
        self.params.callback_params = {"n": n}
        return self

    def scatter(self) -> 'StepTemplate':
        """
        Scatter N outputs to N nodes
        Returns:

        """
        self.params.callback = scatter_callback
        return self

    def aggregate(self) -> 'StepTemplate':
        """
        Aggregate N outputs to 1 node
        Returns:

        """
        self.params.callback = aggregation_callback
        return self

    @abstractmethod
    def create_workflow(self, **kwargs) -> 'Workflow':
        pass

    def callback(self, step: 'Step') -> Union[List[TaskInput], TaskInput]:
        return default_callback(step)

    @staticmethod
    @abstractmethod
    def parse(result) -> Any:
        pass


class StepBuilder:
    """
    A builder class for creating and configuring pipeline steps.

    This class provides a fluent interface for step creation and configuration,
    allowing for easy setup of step properties such as callbacks and configurations.
    """

    def __init__(
            self,
            name: Optional[str] = None,
            input: Optional[Union[TaskInput, List[TaskInput]]] = None,
            workflow: Optional[Union[Callable, Workflow]] = None,
            config: StepConfig = StepConfig()
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
            config=config
        )
        logger.debug(f"Created StepBuilder with name: {self.step.name}")

    def scatter(self, config: Optional[Dict] = None) -> 'StepBuilder':
        """
        Set the callback to scatter_callback.

        The scatter callback takes a single input as a list and publishes each element to multiple outputs.

        Args:
            config (Optional[Dict]): Additional configuration for the scatter callback.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        self.step.callback = scatter_callback
        self.step.callback_type = CallbackType.SCATTER
        self.step.callback_params = config or {}
        logger.debug(f"Set scatter callback for step: {self.step.name}")
        return self

    def broadcast(self, config: Optional[Dict] = None) -> 'StepBuilder':
        """
        Set the callback to broadcast_callback.

        The broadcast callback takes a single input and broadcasts it to multiple outputs.

        Args:
            config (Optional[Dict]): Additional configuration for the broadcast callback.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        self.step.callback = broadcast_callback
        self.step.callback_type = CallbackType.BROADCAST
        self.step.callback_params = config or {}
        logger.debug(f"Set broadcast callback for step: {self.step.name}")
        return self

    def aggregate(self) -> 'StepBuilder':
        """
        Set the callback to aggregation_callback.

        The aggregation callback takes multiple inputs and aggregates them into a single output.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        self.step.callback = aggregation_callback
        self.step.callback_type = CallbackType.AGGREGATE
        logger.debug(f"Set aggregate callback for step: {self.step.name}")
        return self

    def custom(self, callback: Callable, params: Optional[Dict] = None) -> 'StepBuilder':
        """
        Set a custom callback for the step.

        Args:
            callback (Callable): Custom callback function.
            params (Optional[Dict]): Extra parameters for the custom callback.

        Returns:
            StepBuilder: Self instance for method chaining.
        """
        if not callable(callback) or not any(
                param.annotation == Step for param in inspect.signature(callback).parameters.values()):
            raise ValueError("Custom callback must be callable and have a parameter of type Step")
        self.step.callback = callback
        self.step.callback_type = CallbackType.CUSTOM
        self.step.callback_params = params or {}
        logger.debug(f"Set custom callback for step: {self.step.name}")
        return self

    def set_config(self, config: StepConfig) -> 'StepBuilder':
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

    This class provides methods to add steps to a pipeline and build the final Pipeline instance.
    """

    def __init__(self, config: PipelineConfig, dria_client: Dria):
        """
        Initialize a new PipelineBuilder instance.

        Args:
            config (PipelineConfig): The configuration for the pipeline.
            dria_client (Dria): The Dria client instance.
        """
        self.steps: List[Step] = []
        self.templates: List[StepTemplate] = []
        self.config = config
        self.dria_client = dria_client
        self.pipeline_input: Optional[TaskInput] = None
        logger.info("Initialized PipelineBuilder")

    def _check_unique_step_names(self):
        """
        Check if all step names in the pipeline are unique.

        Raises:
            ValueError: If duplicate step names are found.
        """
        step_names = set()
        for step in self.steps:
            if step.name in step_names:
                raise ValueError(f"Duplicate step name found: {step.name}. Each step must have a unique name.")
            step_names.add(step.name)

    def input(self, **kwargs) -> 'PipelineBuilder':
        self.pipeline_input = TaskInput(**kwargs)
        return self

    def _add_step(self, step: Step) -> 'PipelineBuilder':
        """
        Add a step to the pipeline.

        Args:
            step (Step): Step to add to the pipeline.

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
            step.input_keys = list(set([key for key in step_inputs if key not in step_outputs]))
            if previous_step:
                previous_step.next_step_input = step.input_keys

            if step.callback_type in (CallbackType.BROADCAST, CallbackType.AGGREGATE, CallbackType.SCATTER):
                if len(step.input_keys) > 1:
                    raise ValueError("Broadcast and Aggregate callbacks only support a single input for this step. "
                                     "If you want to use multiple inputs, use a custom callback.")

            self.steps.append(step)
            logger.info(f"Added step: {step.name} to pipeline")
        except Exception as e:
            logger.error(f"Error adding step {step.name}: {str(e)}")
            raise
        return self

    def __lshift__(self, other: StepTemplate):
        """
        Add a step to the pipeline using the given StepTemplate.
        Args:
            other:

        Returns:

        """
        _step = StepBuilder(name=other.__class__.__name__,
                            config=StepConfig(),
                            input=other.params.task_input,
                            workflow=other.workflow)

        if hasattr(other, 'callback'):
            _step = _step.custom(other.callback)

        self._add_step(_step.build())
        self.templates.append(other)
        return self

    def build(self) -> Pipeline:
        """
        Build and return the configured Pipeline instance.

        Returns:
            Pipeline: The fully configured Pipeline instance.

        Raises:
            Exception: If there's an error during pipeline building.
        """
        try:
            pipeline = Pipeline(client=self.dria_client, config=self.config)

            self._check_unique_step_names()
            # Note: Uncomment the following line if you want to enforce no callback on the last step
            # self._check_last_step_callback()

            for step in self.steps:
                pipeline.add_step(step)
            logger.info("Built pipeline successfully")
            return pipeline
        except Exception as e:
            logger.error(f"Error building pipeline: {str(e)}")
            raise
