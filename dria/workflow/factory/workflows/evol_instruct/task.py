from typing import Dict, List, Literal
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult

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


class EvolveInstructOutput(BaseModel):
    mutated_prompt: str = Field(..., description="The mutated prompt")
    original_prompt: str = Field(..., description="The original prompt")
    model: str = Field(..., description="Model used for generation")


class EvolveInstruct(WorkflowTemplate):

    # Output schema
    OutputSchema = EvolveInstructOutput

    def define_workflow(self):
        """
        Creates a workflow for mutating the given prompt using the specified mutation type.

        Returns:
            Workflow: The constructed workflow
        """
        self.add_step("{{prompt}}")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated EvolveInstructOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated outputs
        """
        outputs = []
        for r in result:
            part = r.result.split("## New Prompt:")[-1]
            new_prompt = (
                part.strip()
                .replace("##", "")
                .strip()
                .replace("{", "")
                .replace("}", "")
                .strip()
            )
            original_prompt = r.inputs["prompt"].split("Given Prompt#:\n")[1].strip()
            output = self.OutputSchema(
                mutated_prompt=new_prompt,
                original_prompt=original_prompt,
                model=r.model,
            )
            outputs.append(output)

        return outputs
