from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    GetAll,
    Read,
)
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class BioOutput(BaseModel):
    bio: str = Field(..., description="Generated backstory")
    model: str = Field(..., description="Model used for generation")


class ShortBio(WorkflowTemplate):
    # Output schema
    OutputSchema = BioOutput

    def define_workflow(self):
        """
        Creates a workflow for generating backstory.

        Returns:
            Workflow: The constructed workflow
        """

        self.add_step(
            prompt=get_abs_path("prompt.md"),
            inputs=["simulation_description", self.get_list("persona_traits")],
            outputs=["backstory"]
        )

        # Set return value
        self.set_output("backstory")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated BackstoryOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated backstory outputs
        """
        if not result:
            raise ValueError("Backstory generation failed")

        return [self.OutputSchema(bio=r.result, model=r.model) for r in result]
