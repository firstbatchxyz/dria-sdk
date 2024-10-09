from dria.factory.workflows.magpie_instruct import magpie_instruct
from dria.models import TaskInput
import json
from typing import Union, Any
from dria_workflows import Workflow
from typing import List
from dria.pipelines import Step, StepTemplate


class MagPie(StepTemplate):

    def create_workflow(
        self, instructor_persona: str, responding_persona: str
    ) -> "Workflow":
        return magpie_instruct(
            instructor_persona=instructor_persona,
            responding_persona=responding_persona,
            num_turns=self.params.num_turns,
        )

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
