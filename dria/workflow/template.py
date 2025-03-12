import json
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Type, ClassVar, Literal, Union

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
from dria_workflows.workflows.interface import Input
from pydantic import BaseModel, Field

from dria.models import TaskResult


# Default output schema for WorkflowTemplate
class TaskOutput(BaseModel):
    """Default output schema for WorkflowTemplate."""

    inputs: str = Field(..., description="The inputs used to generate the output")
    output: str = Field(..., description="The generated output")
    model: str = Field(..., description="The model used to generate the output")


class WorkflowTemplate(ABC):
    """
    Abstract base class for building AI workflows using the Factory Pattern.

    This class serves as the abstract product in the Factory Pattern implementation,
    defining a common interface that all concrete workflow implementations must follow.
    The Factory Pattern allows for creating different workflow objects without exposing
    the instantiation logic to the client code.

    The WorkflowTemplate provides a structured way to define workflows with steps,
    connections, and configuration options. It abstracts away the complexity of
    workflow construction, allowing developers to focus on defining the specific
    workflow logic rather than the underlying implementation details.

    Factory Pattern Implementation:
    - This abstract class defines the interface for all workflow products
    - Concrete subclasses implement the 'define_workflow' method to create specific workflows
    - Client code can use any concrete workflow implementation interchangeably
    - New workflow types can be added without modifying client code

    Attributes:
        OutputSchema: The schema class for workflow output validation.
        max_tokens: Maximum number of tokens allowed for the workflow.
        max_steps: Maximum number of steps allowed in the workflow.
        max_time: Maximum execution time in seconds for the workflow.

    Internal variables:
        _memory: Dictionary storing workflow memory/state.
        _builder: Instance of WorkflowBuilder for constructing the workflow.
        _step_count: Counter tracking number of steps added.
        _edges: List of Edge objects defining workflow connections.

    Usage Example:
        ```python
        class MyWorkflow(WorkflowTemplate):
            def define_workflow(self):
                step1 = self.add_step(
                    "Generate a response to: {{prompt}}",
                    inputs=["prompt"],
                )

        # Client code
        workflow = MyWorkflow(prompt="Tell me a story")
        result = client.execute(workflow)
        ```
    """

    OutputSchema: ClassVar[Type[BaseModel]] = TaskOutput
    max_tokens: ClassVar[Optional[int]] = None
    max_steps: ClassVar[Optional[int]] = None
    max_time: ClassVar[Optional[int]] = None

    def __init__(self, **kwargs):
        """
        Initialize a new workflow template instance.

        This constructor sets up the internal state needed for workflow construction.
        It accepts arbitrary keyword arguments that will be stored in the workflow's
        memory and made available to steps during execution.

        Args:
            **kwargs: Arbitrary keyword arguments to initialize the workflow's memory.
                     These values can be referenced in prompts using {{key}} syntax.
        """
        self._memory = kwargs
        self._builder = WorkflowBuilder(self._memory)
        self._step_count = 0
        self._edges: List[Edge] = []
        self._task_output_key: Union[str, None] = None

        # Apply configuration if set in class variables
        if self.max_tokens is not None:
            self._builder.set_max_tokens(self.max_tokens)
        if self.max_steps is not None:
            self._builder.set_max_steps(self.max_steps)
        if self.max_time is not None:
            self._builder.set_max_time(self.max_time)

    def build(self) -> Workflow:
        """
        Build and return the complete workflow.

        This method orchestrates the workflow construction process:
        1. Calls the abstract define_workflow method that subclasses must implement
        2. Automatically adds appropriate edge connections if needed
        3. Finalizes the workflow configuration

        Returns:
            Workflow: The fully constructed workflow ready for execution
        """
        self.define_workflow()

        if len(self._edges) == 0 and self._step_count == 1:
            self._edges.append(Edge(source="0", target="_end"))

        elif not any(edge.target == "_end" for edge in self._edges):
            self._edges.append(Edge(source=str(self._step_count - 1), target="_end"))

        self._builder.flow(self._edges)
        self._builder.set_return_value(self._task_output_key)
        return self._builder.build()

    def set_max_tokens(self, max_tokens: int) -> "WorkflowTemplate":
        """
        Set the maximum number of tokens for the workflow.

        This setting limits the total token consumption across all steps
        in the workflow, providing a safeguard against excessive resource usage.

        Args:
            max_tokens: Maximum number of tokens allowed

        Returns:
            self: Returns self for method chaining
        """
        self._builder.set_max_tokens(max_tokens)
        return self

    def set_max_steps(self, max_steps: int) -> "WorkflowTemplate":
        """
        Set the maximum number of steps for the workflow.

        This setting limits the total number of execution steps in the workflow,
        providing a safeguard against infinite loops or excessive complexity.

        Args:
            max_steps: Maximum number of steps allowed

        Returns:
            self: Returns self for method chaining
        """
        self._builder.set_max_steps(max_steps)
        return self

    def set_max_time(self, max_time: int) -> "WorkflowTemplate":
        """
        Set the maximum execution time for the workflow.

        This setting limits the total execution time of the workflow in seconds,
        providing a safeguard against long-running workflows.

        Args:
            max_time: Maximum execution time in seconds

        Returns:
            self: Returns self for method chaining
        """
        self._builder.set_max_time(max_time)
        return self

    @abstractmethod
    def define_workflow(self) -> None:
        """
        Define the workflow steps and connections.

        This is the core abstract method that all concrete workflow implementations
        must override. It defines the specific steps, their inputs/outputs, and
        the connections between them that make up the workflow.

        In the Factory Pattern, this method represents the product-specific
        implementation that each concrete factory provides.

        Example:
            def define_workflow(self):
                # First step using class attribute
                step1 = self.add_step(
                    "{{first_prompt}}",
                    inputs=["first_prompt"],
                    output=["response"]
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
        """
        Process the workflow results.

        This method transforms the raw workflow results into the desired output format
        as defined by the OutputSchema. Subclasses can override this method to
        provide custom result processing logic.

        Args:
            result: List of raw workflow results

        Returns:
            Processed output in the format defined by OutputSchema
        """
        # Default implementation that returns a list of DefaultOutput objects
        return [
            self.OutputSchema(
                inputs=json.dumps(r.inputs), output=r.result, model=r.model
            )
            for r in result
        ]

    def add_step(
        self,
        prompt: str,
        operation: Operator = Operator.GENERATION,
        inputs: Union[Optional[List[str]], list[GetAll]] = None,
        output: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        is_list: bool = False,
        search_type: Literal["search", "news", "scholar"] = "search",
        search_lang: Optional[str] = None,
        search_n_results: Optional[int] = None,
    ) -> str:
        """
        Add a step to the workflow with simplified parameters.

        This method is a key part of the Factory Pattern implementation, providing
        a simplified interface for adding steps to the workflow. It abstracts away
        the complexity of the underlying workflow construction, allowing concrete
        implementations to focus on the high-level workflow definition.

        Args:
            prompt: The prompt template or file path
            operation: Operation type of compute (generation, classification, etc.)
            inputs: List of input variable names to read from memory
            output: Output variable names to write to memory
            schema: Base class for structured outputs (Pydantic model)
            is_list: Whether the output should be treated as a list
            search_type: Type of search to perform (only used with search operation)
            search_lang: Language for search results (only used with search operation)
            search_n_results: Number of search results to return (only used with search operation)

        Returns:
            str: The ID of the created step, used for connecting steps
        """
        step_inputs = []
        if inputs:
            for inp in inputs:
                if isinstance(inp, Input):
                    step_inputs.append(inp)
                else:
                    step_inputs.append(Read.new(key=inp, required=True))

        if output:
            if is_list:
                step_output = Push.new(output)
            else:
                step_output = Write.new(output)
        else:
            step_output = Write.new("result")

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
                outputs=[step_output],
            )
        else:
            self._builder.generative_step(
                operator=operation,
                prompt=prompt,
                inputs=step_inputs,
                outputs=[step_output],
                schema=schema,
            )

        step_id = str(self._step_count)
        self._task_output_key = step_output.key
        self._step_count += 1
        return step_id

    @staticmethod
    def get_list(key: str):
        """
        Helper method to read all items from a list in workflow memory.

        Args:
            key: The key of the list in workflow memory

        Returns:
            GetAll: A GetAll operation that will retrieve all items from the list
        """
        return GetAll.new(key=key, required=True)

    def connect(self, source: str, target: str) -> None:
        """
        Connect two steps in the workflow.

        This method creates a directed edge between two steps, defining the
        execution flow of the workflow.

        Args:
            source: The ID of the source step
            target: The ID of the target step
        """
        self._edges.append(Edge(source=source, target=target))

    def _set_output(self, key: str) -> None:
        """
        Set the final output key for the workflow.

        This method defines which memory key will be returned as the final
        result of the workflow execution.

        Args:
            key: The memory key to return as the workflow result
        """
        self._builder.set_return_value(key)
