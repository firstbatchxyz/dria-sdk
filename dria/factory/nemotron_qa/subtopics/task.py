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


class NemotronSubtopicStep(StepTemplate):
    def create_workflow(self, topic: str, n_subtopics: str) -> Workflow:
        builder = WorkflowBuilder(topic=topic, n_subtopics=n_subtopics)
        builder.set_max_time(50)

        builder.generative_step(
            id="generate_subtopics",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("subtopics")],
        )

        flow = [
            Edge(source="generate_subtopics", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("subtopics")

        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        1 -> N
        Args:
            step:

        Returns:

        """
        return [
            TaskInput(**{"sub_topic": topic, "n_questions": self.params.n_questions})
            for topic in step.output[0].result.split(",")
        ]
