from typing import List
from pydantic import BaseModel, Field
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


class BacktranslationOutput(BaseModel):
    reasoning: str = Field(..., description="Reasoning for the score")
    score: str = Field(..., description="Evaluation score")
    instruction: str = Field(..., description="Original instruction")
    generation: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for evaluation")


class InstructionBacktranslation(SingletonTemplate):
    # Input fields
    instruction: str = Field(..., description="Original instruction")
    generation: str = Field(..., description="Generated text to evaluate")

    # Output schema
    OutputSchema = BacktranslationOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for evaluating instruction-generation pairs.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            instruction=self.instruction, generation=self.generation
        )

        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("score")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("score")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[BacktranslationOutput]:
        """
        Parse the results into validated BacktranslationOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[BacktranslationOutput]: List of validated outputs
        """

        def parse_result(text: str) -> tuple[str, str]:
            split = text.split("Score: ")
            reasoning = split[0].strip()
            score = split[1].strip()
            return score, reasoning

        return [
            BacktranslationOutput(
                reasoning=parse_result(r.result)[1],
                score=parse_result(r.result)[0],
                instruction=self.instruction,
                generation=self.generation,
                model=r.model,
            )
            for r in result
        ]
