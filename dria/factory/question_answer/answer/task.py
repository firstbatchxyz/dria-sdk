from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Read,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path, get_tags, remove_text_between_tags
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class AnswerOutput(BaseModel):
    question: str = Field(..., description="The original question")
    prediction: str = Field(..., description="Generated answer")
    context: str = Field(..., description="Context for answering the question")
    model: str = Field(..., description="Model used for generation")


class Answer(SingletonTemplate):
    # Input fields
    context: str = Field(..., description="Context for answering the question")
    question: str = Field(..., description="Question to be answered")
    persona: str = Field(..., description="Persona to adopt while answering")

    # Output schema
    OutputSchema = AnswerOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating answers to questions.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            context=self.context,
            question=self.question,
            persona=self.persona,
        )

        # Answer Generation Step
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="context", required=True),
                Read.new(key="question", required=True),
                Read.new(key="persona", required=True),
            ],
            outputs=[Write.new("answer")],
        )

        # Define the flow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("answer")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[AnswerOutput]:
        """
        Parse the results into validated AnswerOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[AnswerOutput]: List of validated answer outputs
        """
        returns = []
        for r in result:
            answer = get_tags(r.result, "answer")[0]
            entry = remove_text_between_tags(answer, "rationale")

            if entry is not None:
                returns.append(
                    AnswerOutput(
                        question=self.question,
                        prediction=entry.strip(),
                        context=self.context,
                        model=r.model,
                    )
                )
        return returns
