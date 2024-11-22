from typing import Any, List, Dict
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


class InstructionBacktranslation(SingletonTemplate):

    def workflow(self, instruction: str, generation: str) -> Workflow:
        """

        :param instruction:
        :param generation:
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables
        builder = WorkflowBuilder(instruction=instruction, generation=generation)

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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, Any]]:
        return [
            {
                "reasoning": self.parse(r.result)[1],
                "score": self.parse(r.result)[0],
                "instruction": r.task_input["instruction"],
                "generation": r.task_input["generation"],
                "model": r.model,
            }
            for r in result
        ]

    @staticmethod
    def parse(result):
        split = result.split("Score: ")
        reasoning = split[0].strip()
        score = split[1].strip()

        return score, reasoning
