from typing import List

from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Edge,
    Workflow,
    Write,
)

from dria.factory.utilities import get_abs_path
from dria.models import TaskInput
from dria.pipelines import Step, StepTemplate


class NemotronAnswerStep(StepTemplate):
    def create_workflow(self, question: str) -> Workflow:

        builder = WorkflowBuilder(question=question)
        builder.set_max_time(50)

        builder.generative_step(
            id="generate_answers",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("answers")],
        )

        flow = [
            Edge(source="generate_answers", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("answers")

        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        1 -> N
        Args:
            step:

        Returns:

        """
        responses = []
        for o in step.output:
            resp = o.result
            question = o.task_input["question"]
            resp = resp.replace("RESPONSE A:", "").replace("RESPONSE B:", "")
            try:
                responses.append(
                    TaskInput(
                        **{
                            "question": question.strip(),
                            "response_a": resp.split("\n\n")[0].strip(),
                            "response_b": resp.split("\n\n")[1].strip(),
                        }
                    )
                )
            except:
                pass
        return responses
