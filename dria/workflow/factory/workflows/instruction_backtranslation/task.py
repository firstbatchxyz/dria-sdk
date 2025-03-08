from typing import List

from pydantic import BaseModel, Field

from dria.models import TaskResult
from dria.workflow import WorkflowTemplate
from dria.workflow.factory.utilities import get_abs_path


class BacktranslationOutput(BaseModel):
    reasoning: str = Field(..., description="Reasoning for the score")
    score: str = Field(..., description="Evaluation score")
    instruction: str = Field(..., description="Original instruction")
    generation: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for evaluation")


class InstructionBacktranslation(WorkflowTemplate):

    # Output schema
    OutputSchema = BacktranslationOutput

    def define_workflow(self):
        self.add_step(get_abs_path("prompt.md"))

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated BacktranslationOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated outputs
        """

        def parse_result(text: str) -> tuple[str, str]:
            split = text.split("Score: ")
            reasoning = split[0].strip()
            score = split[1].strip()
            return score, reasoning

        return [
            self.OutputSchema(
                reasoning=parse_result(r.result)[1],
                score=parse_result(r.result)[0],
                instruction=r.task_input["instruction"],
                generation=r.task_input["generation"],
                model=r.model,
            )
            for r in result
        ]
