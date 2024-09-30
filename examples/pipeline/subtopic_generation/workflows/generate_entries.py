import logging

from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Workflow, Read


def generate_entries(
        input_data: dict,
        max_time: int = 300,
        max_steps: int = 20,
        max_tokens: int = 750,
) -> Workflow:
    """Generate entries for a given topic.

    Args:
        input_data (dict): The input data for the workflow.
        max_time (int, optional): The maximum time to run the workflow. Defaults to 300.
        max_steps (int, optional): The maximum number of steps to run the workflow. Defaults to 20.
        max_tokens (int, optional): The maximum number of tokens to run the workflow. Defaults to 750.

    Returns:
        Workflow: The built workflow for entry generation.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    builder = WorkflowBuilder(memory=input_data)
    builder.set_max_time(max_time)
    builder.set_max_steps(max_steps)
    builder.set_max_tokens(max_tokens)

    # Step A: GenerateEntries
    builder.generative_step(
        id="generate_entries",
        path="workflows/prompts/generate_entries.md",
        operator=Operator.GENERATION,
        inputs=[
            Read.new(key="topic", required=True),
        ],
        outputs=[Write.new("entries")]
    )

    flow = [
        Edge(source="generate_entries", target="_end")
    ]
    builder.flow(flow)
    builder.set_return_value("entries")
    workflow = builder.build()

    return workflow
