import logging

from dria_workflows import WorkflowBuilder, Operator, Write, Edge


def poem(input_text: str):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    builder = WorkflowBuilder()

    # Add a step to your workflow
    builder.generative_step(id="write_poem", prompt=input_text, operator=Operator.GENERATION,
                            outputs=[Write.new("poem")])

    # Define the flow of your workflow
    flow = [Edge(source="write_poem", target="_end")]
    builder.flow(flow)

    # Set the return value of your workflow
    builder.set_return_value("poem")

    return builder.build_to_dict()
