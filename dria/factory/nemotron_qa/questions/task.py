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


class NemotronQuestionStep(StepTemplate):
    def create_workflow(self, sub_topic: str, n_questions: str) -> Workflow:
        builder = WorkflowBuilder(sub_topic=sub_topic, n_questions=n_questions)
        builder.set_max_time(50)

        builder.generative_step(
            id="generate_questions",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("questions")],
        )

        flow = [
            Edge(source="generate_questions", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("questions")

        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        1 -> N
        Args:
            step:

        Returns:

        """
        questions = []
        for o in step.output:
            questions.extend(
                [
                    TaskInput(**{"question": q})
                    for q in o.result.split("\n")
                    if q.strip()
                ]
            )
        return questions
