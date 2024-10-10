from typing import Any

from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class GenerateGraph(SingletonTemplate):

    def workflow(self, context: str) -> Workflow:
        """
        Generate a Task to extract terms and their relations from the given context, formatted as specified:

        {
           "node_1": "A concept from extracted ontology",
           "node_2": "A related concept from extracted ontology",
           "edge": "relationship between the two concepts, node_1 and node_2 in one or two sentences"
        }

        :param context: The context from which to extract the ontology of terms.
        :return: A Task object representing the workflow.
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(context=context)
        builder.set_max_tokens(750)
        builder.set_max_time(75)
        # Add a generative step using the prompt
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("graph")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("graph")
        return builder.build()

    def parse_result(self, result: Any):
        return result[0].strip()
