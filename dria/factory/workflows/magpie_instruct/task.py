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
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class DialogueTurn(BaseModel):
    instructor: str = Field(..., description="Instructor's message")
    responder: str = Field(..., description="Responder's message")


class DialogueOutput(BaseModel):
    dialogue: List[DialogueTurn] = Field(..., description="List of dialogue turns")
    model: str = Field(..., description="Model used for generation")


class MagPie(SingletonTemplate):
    # Input fields
    instructor_persona: str = Field(..., description="Persona of the instructor")
    responding_persona: str = Field(..., description="Persona of the responder")
    num_turns: conint(ge=1) = Field(
        default=1, description="Number of conversation turns"
    )

    # Output schema
    OutputSchema = DialogueOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating dialogue between personas.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            instructor_persona=self.instructor_persona,
            responding_persona=self.responding_persona,
        )

        builder.generative_step(
            path=get_abs_path("instruction.md"),
            operator=Operator.GENERATION,
            inputs=[GetAll.new("chat", required=False)],
            outputs=[Push.new("instruction"), Push.new("chat")],
        )

        builder.generative_step(
            path=get_abs_path("response.md"),
            operator=Operator.GENERATION,
            inputs=[GetAll.new("chat", required=False)],
            outputs=[Push.new("responses"), Push.new("chat")],
        )

        flow = [
            Edge(source="0", target="1"),
            Edge(
                source="1",
                target="_end",
                condition=ConditionBuilder.build(
                    expected=str(self.num_turns),
                    expression=Expression.GREATER_THAN_OR_EQUAL,
                    input=Size.new(key="responses", required=True),
                    target_if_not="0",
                ),
            ),
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("chat")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[DialogueOutput]:
        """
        Parse the results into validated DialogueOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[DialogueOutput]: List of validated dialogue outputs
        """
        return [
            DialogueOutput(
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
