from abc import ABC, abstractmethod
from typing import List, Optional, Any, Type, ClassVar, get_args
from pydantic import BaseModel

from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Edge,
    Input,
    Output,
    Read,
    Write,
    Push,
    GetAll,
    Workflow,
    Tools
)
from dria.models import TaskResult


class WorkflowTemplate(ABC):
    """A simplified abstract base class for building workflows.
    Supports class attributes for prompts and output schema.
    """
    OutputSchema: ClassVar[Type[BaseModel]] = None
    max_tokens: ClassVar[Optional[int]] = None
    max_steps: ClassVar[Optional[int]] = None
    max_time: ClassVar[Optional[int]] = None
    tools: ClassVar[Optional[List[Tools]]] = None

    def __init__(self, **kwargs):
        self._memory = kwargs
        self._builder = WorkflowBuilder(self._memory)
        self._step_count = 0
        self._edges: List[Edge] = []

        # Apply configuration if set in class variables
        if self.max_tokens is not None:
            self._builder.set_max_tokens(self.max_tokens)
        if self.max_steps is not None:
            self._builder.set_max_steps(self.max_steps)
        if self.max_time is not None:
            self._builder.set_max_time(self.max_time)
        if self.tools is not None:
            self._builder.set_tools(self.tools)
    def build(self) -> Workflow:
        """Build and return the complete workflow."""
        self.define_workflow()

        if len(self._edges) == 0 and self._step_count == 1:
            self._edges.append(Edge(source="0", target="_end"))

        elif not any(edge.target == "_end" for edge in self._edges):
            self._edges.append(Edge(source=str(self._step_count - 1), target="_end"))

        self._builder.flow(self._edges)
        return self._builder.build()

    def set_max_tokens(self, max_tokens: int) -> 'WorkflowTemplate':
        """Set the maximum number of tokens for the workflow.

        Args:
            max_tokens: Maximum number of tokens allowed

        Returns:
            self for method chaining
        """
        self._builder.set_max_tokens(max_tokens)
        return self

    def set_max_steps(self, max_steps: int) -> 'WorkflowTemplate':
        """Set the maximum number of steps for the workflow.

        Args:
            max_steps: Maximum number of steps allowed

        Returns:
            self for method chaining
        """
        self._builder.set_max_steps(max_steps)
        return self

    def set_max_time(self, max_time: int) -> 'WorkflowTemplate':
        """Set the maximum execution time for the workflow.

        Args:
            max_time: Maximum execution time in seconds

        Returns:
            self for method chaining
        """
        self._builder.set_max_time(max_time)
        return self

    def set_tools(self, tools: List[Tools]) -> 'WorkflowTemplate':
        """Set the tools for the workflow.

        Args:
            tools: List of tools to enable

        Returns:
            self for method chaining

        Raises:
            ValueError: If an invalid tool is specified
        """
        for tool in tools:
            if str(tool) not in set(get_args(Tools)):
                raise ValueError(
                    f"Tool '{tool}' is not a valid tool. Choose from: {', '.join(set(get_args(Tools)))}"
                )
        self._builder.set_tools(tools)
        return self

    @abstractmethod
    def define_workflow(self) -> None:
        """Define the workflow steps and connections.

        Example:
            def define_workflow(self):
                # First step using class attribute
                step1 = self.add_step(
                    "{{first_prompt}}",
                    inputs=["first_prompt"],
                    outputs=["response"]
                )

                # Second step using another prompt
                step2 = self.add_step(
                    "{{second_prompt}} {{response}}",
                    inputs=["second_prompt", "response"],
                    outputs=["result"]
                )

                self.connect(step1, step2)
                self.set_output("result")
        """
        pass

    @abstractmethod
    def callback(self, result: List[TaskResult]) -> Any:
        """Process the workflow results.

        Args:
            result: List of raw workflow results

        Returns:
            Processed output in the desired format
        """
        pass
    def add_step(
            self,
            prompt: str,
            inputs: Optional[List[str]] = None,
            outputs: Optional[List[str]] = None,
            is_list: bool = False,
    ) -> str:
        """Add a step to the workflow with simplified parameters.

        Args:
            prompt: The prompt template or file path
            inputs: List of input variable names
            outputs: List of output variable names
            is_list: Whether the output should be treated as a list

        Returns:
            str: The ID of the created step
        """
        step_inputs = []
        if inputs:
            for inp in inputs:
                step_inputs.append(Read.new(key=inp, required=True))

        step_outputs = []
        if outputs:
            for out in outputs:
                if is_list:
                    step_outputs.append(Push.new(out))
                else:
                    step_outputs.append(Write.new(out))
        else:
            step_outputs = [Write.new("result")]

        if prompt.endswith(('.txt', '.md', '.prompt')):
            try:
                with open(prompt, 'r') as f:
                    prompt = f.read()
            except FileNotFoundError:
                pass

        self._builder.generative_step(
            operator=Operator.GENERATION,
            prompt=prompt,
            inputs=step_inputs,
            outputs=step_outputs
        )

        step_id = str(self._step_count)
        self._step_count += 1
        return step_id

    @staticmethod
    def get_list(key: str) -> Input:
        """Helper method to read all items from a list."""
        return GetAll.new(key=key, required=True)

    def connect(self, source: str, target: str) -> None:
        """Connect two steps in the workflow."""
        self._edges.append(Edge(source=source, target=target))

    def set_output(self, key: str) -> None:
        """Set the final output key for the workflow."""
        self._builder.set_return_value(key)