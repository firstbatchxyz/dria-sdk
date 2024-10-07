from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge


def generate_term_relations_graph(context: str) -> Workflow:
    """
    Generate a Task to extract terms and their relations from the given context, formatted as specified.

    :param context: The context from which to extract the ontology of terms.
    :return: A Task object representing the workflow.
    """
    # Initialize the workflow with variables
    builder = WorkflowBuilder(context=context)

    # Add a generative step using the prompt
    builder.generative_step(
        path="prompt.md", operator=Operator.GENERATION, outputs=[Write.new("graph")]
    )

    flow = [Edge(source="0", target="_end")]
    builder.flow(flow)

    # Set the return value of the workflow
    builder.set_return_value("graph")
    return builder.build()
