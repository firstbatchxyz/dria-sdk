from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path, parse_json
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class SubtopicsOutput(BaseModel):
    topic: str
    subtopic: str = Field(..., description="subtopic of topic")
    model: str = Field(..., description="Model used for generation")


class GenerateSubtopics(SingletonTemplate):
    # Input fields
    topic: str = Field(..., description="Main topic to generate subtopics for")

    # Output schema
    OutputSchema = SubtopicsOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating subtopics for a given topic.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(topic=self.topic)

        # Generate subtopics
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("subtopics")],
        )

        # Define the flow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("subtopics")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[SubtopicsOutput]:
        """
        Parse the results into validated SubtopicsOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SubtopicsOutput]: List of validated subtopics outputs
        """
        return [
            SubtopicsOutput(topic=self.topic, subtopic=subtopic, model=r.model)
            for r in result
            for subtopic in parse_json(r.result)
        ]
