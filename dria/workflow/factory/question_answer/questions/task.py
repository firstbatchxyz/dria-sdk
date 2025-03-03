import json
from typing import List
from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult
from dria.workflow.factory.utilities import get_tags


class QuestionOutput(BaseModel):
    question: str = Field(..., description="List of generated questions")
    persona: str = Field(..., description="Persona name")
    context: str = Field(..., description="Question context")
    model: str = Field(..., description="Model used for generation")


class Question(WorkflowTemplate):
    OutputSchema = QuestionOutput

    def define_workflow(self):
        """
        Creates a workflow for generating questions based on context and backstory.
        """
        self.add_step(prompt=get_abs_path("prompt.md"), outputs=["question"])

        self.set_output("question")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated QuestionOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated question outputs
        """
        processed_outputs = []

        for r in result:
            if r.result == "":
                continue

            q_round = json.loads(r.result)

            for q in q_round:
                question = get_tags(q, "generated_question")
                if question is not None:
                    processed_outputs.append(
                        self.OutputSchema(
                            question=question[0].strip(),
                            persona=r.task_input["persona"],
                            context=r.task_input["context"],
                            model=r.model,
                        )
                    )

        return processed_outputs
