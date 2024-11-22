import json
from typing import Any, List, Dict
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


class MagPie(SingletonTemplate):

    def workflow(
        self, instructor_persona: str, responding_persona: str, num_turns=1
    ) -> Workflow:
        """

        :param instructor_persona:
        :param responding_persona:
        :param num_turns:
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            instructor_persona=instructor_persona, responding_persona=responding_persona
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
                    expected=str(num_turns),
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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, Any]]:
        return [
            {
                "dialogue": self.group_into_dialogue(json.loads(r.result)),
                "model": r.model,
            }
            for r in result
        ]

    @staticmethod
    def group_into_dialogue(messages):
        """
        Groups messages into a list of dialogue turns, where each turn has both speakers.

        Args:
            messages (list of str): The list of messages to be grouped.

        Returns:
            list of dict: A list of dialogue turns, where each turn is a dictionary
                         containing both 'instructor' and 'responder' keys.
        """
        dialogue = []

        # Process messages in pairs
        for i in range(0, len(messages), 2):
            turn = {
                "instructor": messages[i] if i < len(messages) else "",
                "responder": messages[i + 1] if i + 1 < len(messages) else "",
            }
            dialogue.append(turn)

        return dialogue
