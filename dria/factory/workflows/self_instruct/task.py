from typing import List
from pydantic import BaseModel, Field, conint
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class InstructionOutput(BaseModel):
    instructions: List[str] = Field(..., description="List of generated instructions")
    model: str = Field(..., description="Model used for generation")


class SelfInstruct(SingletonTemplate):
    # Input fields
    num_instructions: conint(ge=1) = Field(
        ..., description="The number of user queries to generate"
    )
    criteria_for_query_generation: str = Field(
        ..., description="The criteria for generating the queries"
    )
    application_description: str = Field(
        ..., description="A description of the AI application"
    )
    context: str = Field(
        ..., description="The context to which the queries should be applicable"
    )

    # Output schema
    OutputSchema = InstructionOutput

    def workflow(self) -> Workflow:
        """
        Generate a Task to develop user queries for a given AI application and context.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            num_instructions=str(self.num_instructions),
            criteria_for_query_generation=self.criteria_for_query_generation,
            application_description=self.application_description,
            context=self.context,
        )

        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("user_queries")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("user_queries")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[InstructionOutput]:
        """
        Parse the results into validated InstructionOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[InstructionOutput]: List of validated instruction outputs
        """
        return [
            InstructionOutput(
                instructions=list(filter(None, r.result.strip().split("\n"))),
                model=r.model,
            )
            for r in result
        ]
