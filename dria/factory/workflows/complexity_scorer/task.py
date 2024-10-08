from typing import List
from dria.factory.utilities import get_abs_path
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge


def evolve_complexity(instruction: str) -> Workflow:
    """

    :param instruction:
    :return:
    """

    builder = WorkflowBuilder(instruction=instruction)
    # Prompt to increase the complexity of the instruction
    builder.generative_step(
        path=get_abs_path("evolve.md"),
        operator=Operator.GENERATION,
        outputs=[Write.new("evolved_instruction")],
    )
    flow = [Edge(source="0", target="_end")]
    builder.flow(flow)
    builder.set_return_value("evolved_instruction")
    return builder.build()


def score_complexity(instructions: List[str]) -> Workflow:
    """

    :param instructions:
    :return:
    """
    # Build the prompt to score the instructions
    instruction_list = [f"[{i+1}] {instr}" for i, instr in enumerate(instructions)]
    builder = WorkflowBuilder(instruction_list=instruction_list)
    builder.generative_step(
        path=get_abs_path("score.md"),
        operator=Operator.GENERATION,
        outputs=[Write.new("scores")],
    )
    flow = [Edge(source="0", target="_end")]
    builder.flow(flow)
    builder.set_return_value("scores")
    return builder.build()


def parse_scores(scores_text):
    import re

    scores = {}
    lines = scores_text.strip().split("\n")
    for line in lines:
        match = re.match(r"\[(\d+)\]\s*Score:\s*(\d+)", line)
        if match:
            idx = int(match.group(1)) - 1
            score = int(match.group(2))
            scores[idx] = score
    return scores
