import logging
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, GetAll, Workflow
from typing import List, Union

from dria.models import TaskInput
from dria.pipelines import StepTemplate, Step
from dria.factory.utilities import get_abs_path
from dria.utils.task_utils import parse_json


class GenerateSubtopics(StepTemplate):
    def create_workflow(self, topic: str) -> Workflow:
        """Generate subtopics for a given topic.

        Args:
            topic (list): The input data for the workflow.
        Returns:
            Workflow: The built workflow for subtopic generation.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        builder = WorkflowBuilder(topic=topic)

        # Step A: GenerateSubtopics
        builder.generative_step(
            id="generate_subtopics",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("subtopics")],
        )

        flow = [Edge(source="generate_subtopics", target="_end")]
        builder.flow(flow)
        builder.set_return_value("subtopics")
        workflow = builder.build()
        return workflow

    def callback(self, step: "Step") -> Union[List[TaskInput], TaskInput]:
        """
        Only to use as the last callback
        Args:
            step:

        Returns:

        """
        # flatten list of lists
        outputs = [parse_json(o.result) for o in step.output]
        flattened = [item for sublist in outputs for item in sublist]
        return TaskInput(**{"subtopics": flattened})
