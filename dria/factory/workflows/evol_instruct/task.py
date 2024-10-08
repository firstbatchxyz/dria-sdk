from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from typing import Dict

# Mutation templates
MUTATION_TEMPLATES: Dict[str, str] = {
    "FRESH_START": """Write one question or request containing one or more of the following words: {{prompt}}""",
    "ADD_CONSTRAINTS": """Add a few more constraints or requirements to #Given Prompt#, and create #New Prompt#.

    #Given Prompt#:
    {{prompt}}""",
    "DEEPEN": """Slightly increase the depth and breadth of #Given Prompt#, and create #New Prompt#.
    
    #Given Prompt#:
    {{prompt}}""",
    "CONCRETIZE": """Make #Given Prompt# slightly more concrete, and create #New Prompt#.
    
    #Given Prompt#:
    {{prompt}}""",
    "INCREASE_REASONING": """If #Given Prompt# can be solved with just a few simple thinking processes, rewrite it to explicitly request multi-step reasoning, and create #New Prompt#.
    
    #Given Prompt#:
    {{prompt}}""",
    "SWITCH_TOPIC": """Rewrite #Given Prompt# by switching the topic, keeping the domain and difficulty level similar, and create #New Prompt#.
    
    #Given Prompt#:
    {{prompt}}""",
}


def evolve_instruct(prompt: str, mutation_type: str) -> Workflow:
    """
    Mutate the given prompt using the specified mutation type.

    :param prompt: The original prompt to be mutated.
    :param mutation_type: The type of mutation to apply.
    :return: A Task object representing the mutation workflow.
    """
    if mutation_type not in MUTATION_TEMPLATES:
        raise ValueError(f"Invalid mutation type: {mutation_type}")

    builder = WorkflowBuilder(prompt=prompt)
    builder.generative_step(
        prompt=MUTATION_TEMPLATES[mutation_type],
        operator=Operator.GENERATION,
        outputs=[Write.new("mutated_prompt")],
    )
    flow = [Edge(source="0", target="_end")]
    builder.flow(flow)
    builder.set_return_value("mutated_prompt")
    return builder.build()
