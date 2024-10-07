import logging
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Read, Workflow
from dria.pipelines import StepTemplate


logger = logging.getLogger(__name__)


class GenerateEntries(StepTemplate):

    def create_workflow(self, topic: str) -> Workflow:
        """Generate entries for a given topic.

        Args:
            topic (str): The input data for the workflow.

        Returns:
            Workflow: The built workflow for entry generation.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        builder = WorkflowBuilder(topic=topic)

        # Step A: GenerateEntries
        builder.generative_step(
            id="generate_entries",
            path="workflows/prompts/generate_entries.md",
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="topic", required=True),
            ],
            outputs=[Write.new("entries")],
        )

        flow = [Edge(source="generate_entries", target="_end")]
        builder.flow(flow)
        builder.set_return_value("entries")
        workflow = builder.build()

        return workflow
