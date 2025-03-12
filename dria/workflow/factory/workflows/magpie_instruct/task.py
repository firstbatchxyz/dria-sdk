import json
from typing import List
from pydantic import BaseModel, Field, conint
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    GetAll,
    Push,
    Edge,
    ConditionBuilder,
    Expression,
    Size,
)
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class DialogueTurn(BaseModel):
    instructor: str = Field(..., description="Instructor's message")
    responder: str = Field(..., description="Responder's message")


class DialogueOutput(BaseModel):
    dialogue: List[DialogueTurn] = Field(..., description="List of dialogue turns")
    model: str = Field(..., description="Model used for generation")


class MagPie(WorkflowTemplate):
    # Output schema
    OutputSchema = DialogueOutput

    def define_workflow(self):
        """
        Creates a workflow for generating dialogue between personas.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables

        self.add_step(prompt=get_abs_path("instruction.md"), output="instruction")
        self.add_step(prompt=get_abs_path("response.md"), inputs=["instruction"])

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated DialogueOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated dialogue outputs
        """
        return [
            self.OutputSchema(
                dialogue=group_into_dialogue(json.loads(r.result)), model=r.model
            )
            for r in result
        ]


def group_into_dialogue(messages: List[str]) -> List[DialogueTurn]:
    """
    Groups messages into a list of dialogue turns.

    Args:
        messages: List of messages to be grouped

    Returns:
        List[DialogueTurn]: List of validated dialogue turns
    """
    dialogue = []

    # Process messages in pairs
    for i in range(0, len(messages), 2):
        turn = DialogueTurn(
            instructor=messages[i] if i < len(messages) else "",
            responder=messages[i + 1] if i + 1 < len(messages) else "",
        )
        dialogue.append(turn)

    return dialogue
