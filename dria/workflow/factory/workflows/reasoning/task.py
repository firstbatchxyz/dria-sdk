from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Push,
    Edge,
)
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class ReasoningSchema(BaseModel):
    reasoning: str = Field(..., alias="reasoning", description="Reasoning chain")
    model: str = Field(..., description="Model used for generation")


class Reasoning(WorkflowTemplate):
    prompt: str = Field(..., description="Prompt to reason about")

    # Output schema
    OutputSchema = ReasoningSchema

    def build(self) -> Workflow:
        """
        Creates a workflow for reasoning about a prompt.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(prompt=self.prompt)

        # Set workflow constraints
        builder.set_max_time(180)
        builder.set_max_steps(20)
        builder.set_max_tokens(1500)

        # Reasoning Generation step
        builder.generative_step(
            id="reasoning_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Push.new("reasoning")],
        )

        # Define flow
        flow = [
            Edge(
                source="reasoning_generation",
                target="_end",
            )
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("reasoning")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated ReasoningSchema objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated reasoning results
        """
        results = []
        for r in result:
            results.append(self.OutputSchema(**{"reasoning": r.result, "model": r.model}))
        return results
