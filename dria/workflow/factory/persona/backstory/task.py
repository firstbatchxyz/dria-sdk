from typing import List
from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import get_abs_path, parse_json
from dria.workflow import WorkflowTemplate
from dria.models import TaskResult
from dria.utilities import logger


class BackstoryOutput(BaseModel):
    backstory: str = Field(..., description="Generated backstory")
    model: str = Field(..., description="Model used for generation")


class BackStory(WorkflowTemplate):

    # Output schema
    OutputSchema = BackstoryOutput

    def define_workflow(self):
        """
        Creates a workflow for generating backstory.

        """
        self.add_step(
            prompt=get_abs_path("prompt.md"),
            inputs=["simulation_description", "persona_traits"],
            outputs=["backstory"]
        )

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

        outputs = []
        for r in result:
            try:
                backstory = parse_json(r.result)["backstory"]
            except Exception as e:
                logger.debug(e)
                backstory = r.result

            outputs.append(self.OutputSchema(backstory=backstory, model=r.model))

        return outputs
