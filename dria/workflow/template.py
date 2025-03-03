from abc import ABC, abstractmethod
from typing import List, Optional, Any, Type, ClassVar, Literal

from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Edge,
    Read,
    Write,
    Push,
    GetAll,
    Workflow,
)
from pydantic import BaseModel, Field

from dria.models import TaskResult


# Default output schema for WorkflowTemplate
class DefaultOutput(BaseModel):
    """Default output schema for WorkflowTemplate."""

    output: str = Field(..., description="The generated output")


class WorkflowTemplate(ABC):
    """A simplified abstract base class for building workflows.

    Each workflow template provides a structured way to define workflows with steps, connections, and configuration options.
    The template supports class attributes for prompts, output schema and various execution limits.

    Attributes:
        OutputSchema: The schema class for workflow output validation.
        max_tokens: Maximum number of tokens allowed for the workflow.
        max_steps: Maximum number of steps allowed in the workflow.
        max_time: Maximum execution time in seconds for the workflow.
        _memory: Dictionary storing workflow memory/state.
        _builder: Instance of WorkflowBuilder for constructing the workflow.
        _step_count: Counter tracking number of steps added.
        _edges: List of Edge objects defining workflow connections.
    """

    OutputSchema: ClassVar[Type[BaseModel]] = None
    max_tokens: ClassVar[Optional[int]] = None
    max_steps: ClassVar[Optional[int]] = None
    max_time: ClassVar[Optional[int]] = None

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

    def build(self) -> Workflow:
        """Build and return the complete workflow."""
        self.define_workflow()

        if len(self._edges) == 0 and self._step_count == 1:
            self._edges.append(Edge(source="0", target="_end"))

        elif not any(edge.target == "_end" for edge in self._edges):
            self._edges.append(Edge(source=str(self._step_count - 1), target="_end"))

        self._builder.flow(self._edges)
        return self._builder.build()

    def set_max_tokens(self, max_tokens: int) -> "WorkflowTemplate":
        """Set the maximum number of tokens for the workflow.

        Args:
            max_tokens: Maximum number of tokens allowed

        Returns:
            self for method chaining
        """
        self._builder.set_max_tokens(max_tokens)
        return self

    def set_max_steps(self, max_steps: int) -> "WorkflowTemplate":
        """Set the maximum number of steps for the workflow.

        Args:
            max_steps: Maximum number of steps allowed

        Returns:
            self for method chaining
        """
        self._builder.set_max_steps(max_steps)
        return self

    def set_max_time(self, max_time: int) -> "WorkflowTemplate":
        """Set the maximum execution time for the workflow.

        Args:
            max_time: Maximum execution time in seconds

        Returns:
            self for method chaining
        """
        self._builder.set_max_time(max_time)
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

    def callback(self, result: List[TaskResult]) -> Any:
        """Process the workflow results.

        Args:
            result: List of raw workflow results

        Returns:
            Processed output in the desired format
        """
        # Default implementation that returns a list of DefaultOutput objects
        return [self.OutputSchema(output=r.result) for r in result]

    def add_step(
        self,
        prompt: str,
        operation: Operator = Operator.GENERATION,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        schema: Optional[Type[BaseModel]] = None,
        is_list: bool = False,
        search_type: Literal["search", "news", "scholar"] = "search",
        search_lang: Optional[str] = None,
        search_n_results: Optional[int] = None,
    ) -> str:
        """Add a step to the workflow with simplified parameters.

        Args:
            operation: Operation type of compute
            prompt: The prompt template or file path
            inputs: List of input variable names
            outputs: List of output variable names
            schema: Base class for structured outputs
            is_list: Whether the output should be treated as a list
            search_type: Type of search to perform (only used with search operation)
            search_lang: Language for search results (only used with search operation)
            search_n_results: Number of search results to return (only used with search operation)

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

        if prompt.endswith((".txt", ".md", ".prompt")):
            try:
                with open(prompt, "r") as f:
                    prompt = f.read()
            except FileNotFoundError:
                pass

        if operation == Operator.SEARCH:
            self._builder.search_step(
                search_query=prompt,
                search_type=search_type,
                lang=search_lang,
                n_results=search_n_results,
                outputs=step_outputs,
            )
        else:
            self._builder.generative_step(
                operator=operation,
                prompt=prompt,
                inputs=step_inputs,
                outputs=step_outputs,
                schema=schema,
            )

        step_id = str(self._step_count)
        self._step_count += 1
        return step_id

    @staticmethod
    def get_list(key: str):
        """Helper method to read all items from a list."""
        return GetAll.new(key=key, required=True)

    def connect(self, source: str, target: str) -> None:
        """Connect two steps in the workflow."""
        self._edges.append(Edge(source=source, target=target))

    def set_output(self, key: str) -> None:
        """Set the final output key for the workflow."""
        self._builder.set_return_value(key)
