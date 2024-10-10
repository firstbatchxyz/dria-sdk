from dria.models import TaskInput
import json
from typing import Union, Any
from dria_workflows import Workflow
from typing import List
from dria.pipelines import Step, StepTemplate
from dria_workflows import WorkflowBuilder, Operator, GetAll, Push, Edge, ConditionBuilder, Expression, Size
from dria.factory.utilities import get_abs_path


class MagPie(StepTemplate):

    def create_workflow(
        self, instructor_persona: str, responding_persona: str
    ) -> "Workflow":
        """

        :param instructor_persona:
        :param responding_persona:
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
                    expected=str(self.params.num_turns),
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

    def callback(self, step: "Step") -> Union[List[TaskInput], TaskInput]:
        return [self.group_into_dialogue(self.parse(o.result)) for o in step.output][0]

    def parse(self, result) -> Any:
        return json.loads(result)

    def group_into_dialogue(self, messages):
        """
        Groups a list of messages into a dialogue between Speaker A and Speaker B.

        Args:
            messages (list of str): The list of messages to be grouped.

        Returns:
            list of dict: A list where each element is a dictionary representing a turn in the dialogue.
        """
        dialogue = []
        speakers = self.params.speakers or ["A", "B"]

        for index, message in enumerate(messages):
            speaker = speakers[index % 2]
            dialogue.append(TaskInput(**{speaker: message}))

        return dialogue
