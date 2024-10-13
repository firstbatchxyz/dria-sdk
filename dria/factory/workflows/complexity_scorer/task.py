from dria.factory.utilities import get_abs_path
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from typing import Dict, List, Union
import re


class EvolveComplexity(SingletonTemplate):

    def workflow(self, instruction: str) -> Workflow:
        """

        :param instruction:
        :return:
        """
        self.params.instruction = instruction
        builder = WorkflowBuilder(instruction=instruction)
        # Prompt to increase the complexity of the instruction
        builder.generative_step(
            path=get_abs_path("evolve.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("evolved_instruction")],
        )
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("evolved_instruction")
        return builder.build()

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, str]]:
        return [
            {
                "evolved_instruction": r.result.strip(),
                "instruction": self.params.instruction,
                "model": r.model,
            }
            for r in result
        ]


class ScoreComplexity(SingletonTemplate):

    def workflow(self, instructions: List[str]) -> Workflow:
        """

        :param instructions:
        :return:
        """
        self.params.instructions = instructions
        instruction_list = [
            f"[{i + 1}] {instr}" for i, instr in enumerate(instructions)
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

    def parse_result(
        self, result: List[TaskResult]
    ) -> List[List[Dict[str, Union[str, int]]]]:
        scores = {}
        lines = result[0].result.strip().split("\n")
        for line in lines:
            match = re.match(r"\[(\d+)\]\s*Score:\s*(\d+)", line)
            if match:
                idx = int(match.group(1)) - 1
                score = int(match.group(2))
                scores[idx] = score
        return [
            [
                {"instruction": instr, "score": scores.get(i, 0), "model": r.model}
                for i, instr in enumerate(self.params.instructions)
            ]
            for r in result
        ]
