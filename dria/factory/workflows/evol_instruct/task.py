from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from typing import Dict, List, Literal
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, str]]:

        parts = result[0].result.split("## New Prompt:")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid result format: {result[0].result}:' sections found"
            )
        new_prompt = (
            parts[1]
            .strip()
            .replace("##", "")
            .strip()
            .replace("{", "")
            .replace("}", "")
            .strip()
        )
        return [
            {
                "mutated_prompt": new_prompt,
                "prompt": self.params.prompt,
                "model": r.model,
            }
            for r in result
        ]
