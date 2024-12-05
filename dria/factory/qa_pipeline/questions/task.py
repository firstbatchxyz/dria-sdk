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
    Read,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from dria.factory.qa_pipeline.utils import get_text_between_tags


class QuestionOutput(BaseModel):
    questions: List[str] = Field(..., description="List of generated questions")
    model: str = Field(..., description="Model used for generation")


class QuestionGenerator(SingletonTemplate):
    # Input fields
    context: str = Field(..., description="Context for question generation")
    backstory: str = Field(..., description="Backstory for question generation")
    max_time: int = Field(default=300, description="Maximum time to run the workflow")
    max_steps: int = Field(default=30, description="Maximum number of steps")
    max_tokens: int = Field(default=750, description="Maximum number of tokens")

    # Output schema
    OutputSchema = QuestionOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating questions based on context and backstory.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(backstory=self.backstory, context=self.context)

        builder.set_max_time(self.max_time)
        builder.set_max_steps(self.max_steps)
        builder.set_max_tokens(self.max_tokens)

        builder.generative_step(
            id="question_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="context", required=True),
                GetAll.new(key="history", required=False),
                Read.new(key="backstory", required=True),
            ],
            outputs=[Push.new("history")],
        )

        flow = [
            Edge(
                source="question_generation",
                target="_end",
                condition=ConditionBuilder.build(
                    input=Size.new("history", required=True),
                    expression=Expression.GREATER_THAN,
                    expected="1",
                    target_if_not="question_generation",
                ),
            )
        ]

        builder.flow(flow)
        builder.set_return_value("history")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[QuestionOutput]:
        """
        Parse the results into validated QuestionOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[QuestionOutput]: List of validated question outputs
        """
        processed_outputs = []

        for r in result:
            if r.result == "":
                continue

            questions = []
            q_round = json.loads(r.result)

            for q in q_round:
                question = get_text_between_tags(q, "generated_question")
                if question is not None:
                    questions.append(question.strip())

            if questions:
                processed_outputs.append(
                    QuestionOutput(questions=questions, model=r.model)
                )

        return processed_outputs
