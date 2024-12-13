import logging
from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Push,
    Edge,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from dria.factory.utilities import get_tags


class QuestionSet(BaseModel):
    one_hop: str = Field(..., alias="1-hop", description="1-hop question")
    two_hop: str = Field(..., alias="2-hop", description="2-hop question")
    three_hop: str = Field(..., alias="3-hop", description="3-hop question")
    answer: str = Field(..., description="Answer to the questions")
    model: str = Field(..., description="Model used for generation")


class MultiHopQuestion(SingletonTemplate):
    # Input fields
    chunks: List[str] = Field(
        ..., min_length=3, max_length=3, description="List of three document chunks"
    )

    # Output schema
    OutputSchema = QuestionSet

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating multi-hop questions from three documents.

        Returns:
            Workflow: The constructed workflow
        """
        if self.chunks is None or len(self.chunks) != 3:
            raise ValueError("The input documents must be a list of 3 strings.")

        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            document_1=self.chunks[0],
            document_2=self.chunks[1],
            document_3=self.chunks[2],
        )

        # Set workflow constraints
        builder.set_max_time(60)
        builder.set_max_steps(5)
        builder.set_max_tokens(600)

        # Question Generation step
        builder.generative_step(
            id="question_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Push.new("questions")],
        )

        # Define flow
        flow = [
            Edge(
                source="question_generation",
                target="_end",
            )
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("questions")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[QuestionSet]:
        """
        Parse the results into validated QuestionSet objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[QuestionSet]: List of validated question sets
        """
        results = []
        for r in result:
            onehop = get_tags(r.result, "1hop")[0]
            twohop = get_tags(r.result, "2hop")[0]
            threehop = get_tags(r.result, "3hop")[0]
            answer = get_tags(r.result, "answer")[0]

            if None in [onehop, twohop, threehop, answer]:
                logging.debug(
                    "One of the questions is missing. Please check the output."
                )
                continue

            results.append(
                QuestionSet(
                    **{
                        "1-hop": onehop,
                        "2-hop": twohop,
                        "3-hop": threehop,
                        "answer": answer,
                        "model": r.model,
                    }
                )
            )
        return results
