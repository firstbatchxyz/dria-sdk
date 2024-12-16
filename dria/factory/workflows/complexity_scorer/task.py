from typing import Dict, List
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
import re


# Output schemas for EvolveComplexity
class EvolveOutput(BaseModel):
    evolved_instruction: str = Field(
        ..., description="Evolved version of the instruction"
    )
    instruction: str = Field(..., description="Original instruction")
    model: str = Field(..., description="Model used for generation")


class EvolveComplexity(SingletonTemplate):
    # Input fields
    instruction: str = Field(..., description="Instruction to evolve")

    # Output schema
    OutputSchema = EvolveOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for evolving instruction complexity.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(instruction=self.instruction)

        builder.generative_step(
            path=get_abs_path("evolve.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("evolved_instruction")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("evolved_instruction")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[EvolveOutput]:
        """
        Parse the results into validated EvolveOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[EvolveOutput]: List of validated outputs
        """
        return [
            EvolveOutput(
                evolved_instruction=r.result.strip(),
                instruction=self.instruction,
                model=r.model,
            )
            for r in result
        ]


# Output schemas for ScoreComplexity
class InstructionScore(BaseModel):
    instruction: str = Field(..., description="Instruction being scored")
    score: int = Field(..., description="Complexity score")
    model: str = Field(..., description="Model used for scoring")


class ScoreComplexity(SingletonTemplate):
    # Input fields
    instructions: List[str] = Field(..., description="List of instructions to score")

    # Output schema
    OutputSchema = List[InstructionScore]

    def workflow(self) -> Workflow:
        """
        Creates a workflow for scoring instruction complexity.

        Returns:
            Workflow: The constructed workflow
        """
        instruction_list = [
            f"[{i + 1}] {instr}" for i, instr in enumerate(self.instructions)
        ]
        builder = WorkflowBuilder(instruction_list=instruction_list)

        builder.generative_step(
            path=get_abs_path("score.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("scores")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("scores")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[List[InstructionScore]]:
        """
        Parse the results into validated InstructionScore objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[List[InstructionScore]]: List of lists of validated score outputs
        """

        def parse_scores(result_text: str) -> Dict[int, int]:
            scores = {}
            lines = result_text.strip().split("\n")
            for line in lines:
                match = re.match(r"\[(\d+)\]\s*Score:\s*(\d+)", line)
                if match:
                    idx = int(match.group(1)) - 1
                    score = int(match.group(2))
                    scores[idx] = score
            return scores

        return [
            [
                InstructionScore(
                    instruction=instr,
                    score=parse_scores(r.result).get(i, 0),
                    model=r.model,
                )
                for i, instr in enumerate(self.instructions)
            ]
            for r in result
        ]
