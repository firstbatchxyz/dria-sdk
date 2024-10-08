import logging
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, GetAll, Workflow
from typing import List
from dria.pipelines import StepTemplate
from dria.factory.utilities import get_abs_path


class GenerateSubtopics(StepTemplate):
    def create_workflow(self, topics: List[str]) -> Workflow:
        """Generate subtopics for a given topic.

        Args:
            topics (list): The input data for the workflow.
        Returns:
            Workflow: The built workflow for subtopic generation.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        builder = WorkflowBuilder(topics=topics)

        # Step A: GenerateSubtopics
        builder.generative_step(
            id="generate_subtopics",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                GetAll.new(key="topics", required=True),
            ],
            outputs=[Write.new("subtopics")],
        )

        flow = [Edge(source="generate_subtopics", target="_end")]
        builder.flow(flow)
        builder.set_return_value("subtopics")
        workflow = builder.build()

        return workflow
