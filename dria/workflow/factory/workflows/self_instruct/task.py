from typing import List
from pydantic import BaseModel, Field, conint
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class InstructionOutput(BaseModel):
    instructions: List[str] = Field(..., description="List of generated instructions")
    model: str = Field(..., description="Model used for generation")


class SelfInstruct(WorkflowTemplate):

    # Output schema
    OutputSchema = InstructionOutput

    def define_workflow(self):
        """
        Generate a Task to develop user queries for a given AI application and context.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        self.add_step(get_abs_path("prompt.md"))

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated InstructionOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[InstructionOutput]: List of validated instruction outputs
        """
        return [
            self.OutputSchema(
                instructions=list(filter(None, r.result.strip().split("\n"))),
                model=r.model,
            )
            for r in result
        ]
