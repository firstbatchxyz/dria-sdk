from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


def fact_check(context: str) -> Workflow:
    """ """
    # Initialize the workflow with variables
    builder = WorkflowBuilder(context=context)

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
