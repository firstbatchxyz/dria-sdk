import logging

from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Workflow, GetAll


def generate_subtopics(
        input_data: dict,
        max_time: int = 300,
        max_steps: int = 20,
        max_tokens: int = 750,
) -> Workflow:
    """Generate subtopics for a given topic.

    Args:
        input_data (dict): The input data for the workflow.
        max_time (int, optional): The maximum time to run the workflow. Defaults to 300.
        max_steps (int, optional): The maximum number of steps to run the workflow. Defaults to 20.
        max_tokens (int, optional): The maximum number of tokens to run the workflow. Defaults to 750.

    Returns:
        Workflow: The built workflow for subtopic generation.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    builder = WorkflowBuilder(**input_data)
    builder.set_max_time(max_time)
    builder.set_max_steps(max_steps)
    builder.set_max_tokens(max_tokens)

    # Step A: GenerateSubtopics
    builder.generative_step(
        id="generate_subtopics",
        path="workflows/prompts/generate_subtopics.md",
        operator=Operator.GENERATION,
        inputs=[
            GetAll.new(key="topics", required=True),
        ],
        outputs=[Write.new("subtopics")]
    )

    flow = [
        Edge(source="generate_subtopics", target="_end")
    ]
    builder.flow(flow)
    builder.set_return_value("subtopics")
    workflow = builder.build()

    return workflow
