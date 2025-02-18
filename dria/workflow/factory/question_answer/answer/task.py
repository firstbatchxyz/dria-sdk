from typing import List

from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import (
    get_abs_path,
    get_tags,
    remove_text_between_tags,
)
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class AnswerOutput(BaseModel):
    question: str = Field(..., description="The original question")
    prediction: str = Field(..., description="Generated answer")
    context: str = Field(..., description="Context for answering the question")
    model: str = Field(..., description="Model used for generation")


class Answer(WorkflowTemplate):
    # Output schema
    OutputSchema = AnswerOutput

    def define_workflow(self):
        """
        Creates a workflow for generating answers to questions.
        """
        self.add_step(
            prompt=get_abs_path("prompt.md"),
            inputs=["context", "question", "persona"],
            outputs=["answer"]
        )
        self.set_output("answer")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated AnswerOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated answer outputs
        """
        returns = []
        for r in result:
            answer = get_tags(r.result, "answer")[0]
            entry = remove_text_between_tags(answer, "rationale")

            if entry is not None:
                returns.append(
                    self.OutputSchema(
                        question=r.task_input["question"],
                        prediction=entry.strip(),
                        context=r.task_input["context"],
                        model=r.model,
                    )
                )
        return returns
