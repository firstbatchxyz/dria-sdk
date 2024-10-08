from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path


def self_instruct(
    num_instructions: int,
    criteria_for_query_generation: str,
    application_description: str,
    context: str,
) -> Workflow:
    """
    Generate a Task to develop user queries for a given AI application and context.

    :param num_instructions: The number of user queries to generate.
    :param criteria_for_query_generation: The criteria for generating the queries.
    :param application_description: A description of the AI application.
    :param context: The context to which the queries should be applicable.
    :return: A Task object representing the workflow.
    """

    # Initialize the workflow with variables to be used in the prompt
    builder = WorkflowBuilder(
        num_instructions=str(num_instructions),
        criteria_for_query_generation=criteria_for_query_generation,
        application_description=application_description,
        context=context,
    )

    # Add a generative step using the prompt string
    builder.generative_step(
        path=get_abs_path("prompt.md"),
        operator=Operator.GENERATION,
        outputs=[Write.new("user_queries")],
    )

    # Define the flow of the workflow
    flow = [Edge(source="0", target="_end")]
    builder.flow(flow)

    # Set the return value of the workflow
    builder.set_return_value("user_queries")
    return builder.build()
