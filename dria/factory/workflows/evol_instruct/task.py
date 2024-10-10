from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from typing import Dict, Any, Literal
from dria.factory.workflows.template import SingletonTemplate
import re

MutationType = Literal[
    "FRESH_START",
    "ADD_CONSTRAINTS",
    "DEEPEN",
    "CONCRETIZE",
    "INCREASE_REASONING",
    "SWITCH_TOPIC",
]

MUTATION_TEMPLATES: Dict[MutationType, str] = {
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


class EvolveInstruct(SingletonTemplate):

    def workflow(self, prompt: str, mutation_type: MutationType) -> Workflow:
        """
        Mutate the given prompt using the specified mutation type.

        :param prompt: The original prompt to be mutated.
        :param mutation_type: The type of mutation to apply.
        :return: A Task object representing the mutation workflow.
        """
        if mutation_type not in MUTATION_TEMPLATES:
            raise ValueError(f"Invalid mutation type: {mutation_type}")

        self.params.prompt = prompt
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

    def parse_result(self, result: Any) -> Dict[str, str]:
        # extract text bet {}
        result = re.findall(r"\{([^}]+)\}", result[0])
        return {"mutated_prompt": result[0].strip(), "prompt": self.params.prompt}
