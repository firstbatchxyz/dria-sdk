from typing import List

from dria_workflows import Operator
from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import get_abs_path, parse_json
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class SubtopicsOutput(BaseModel):
    topic: str
    subtopic: str = Field(..., description="subtopic of topic")
    model: str = Field(..., description="Model used for generation")


class GenerateSubtopics(WorkflowTemplate):
    # Output schema
    OutputSchema = SubtopicsOutput

    def define_workflow(self):
        """
        Creates a workflow for generating subtopics for a given topic.
        """

        self.add_step(
            prompt=get_abs_path("prompt.md"),
        )

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated SubtopicsOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated subtopics outputs
        """
        return [
            self.OutputSchema(topic=r.inputs["topic"], subtopic=subtopic, model=r.model)
            for r in result
            for subtopic in parse_json(r.result)
        ]
