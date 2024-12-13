import json
from typing import List
from pydantic import BaseModel, Field
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
from dria.factory.utilities import get_tags


class QuestionOutput(BaseModel):
    question: str = Field(..., description="List of generated questions")
    persona: str = Field(..., description="Persona name")
    context: str = Field(..., description="Question context")
    model: str = Field(..., description="Model used for generation")


class Question(SingletonTemplate):
    # Input fields
    context: str = Field(..., description="Context for question generation")
    persona: str = Field(
        "A curious person.", description="Persona for question generation"
    )
    num_questions: int = Field(default=1, lt=50, description="Number of questions")

    # Output schema
    OutputSchema = QuestionOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating questions based on context and backstory.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(persona=self.persona, context=self.context)

        builder.set_max_time(65)
        builder.set_max_steps(self.num_questions * 2 + 1)
        builder.set_max_tokens(500)

        builder.generative_step(
            id="question_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="context", required=True),
                GetAll.new(key="history", required=False),
                Read.new(key="persona", required=True),
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
                    expected=str(self.num_questions),
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

            q_round = json.loads(r.result)

            for q in q_round:
                question = get_tags(q, "generated_question")
                if question is not None:
                    processed_outputs.append(
                        QuestionOutput(
                            question=question[0].strip(),
                            persona=self.persona,
                            context=self.context,
                            model=r.model,
                        )
                    )

        return processed_outputs
