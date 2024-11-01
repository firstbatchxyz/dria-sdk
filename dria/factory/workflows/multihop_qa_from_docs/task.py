import logging
from typing import List

from dria.models import TaskInput, TaskResult
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Edge,
    Workflow,
    Push,
)

from dria.factory.qa_pipeline.utils import get_text_between_tags
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class MultiHopQuestion(SingletonTemplate):

    def workflow(
        self,
        chunks: List[str]
    ) -> Workflow:
        """Generate questions for a 3 documents and backstory.

        Args:
            chunks (List[str]): The input data to be used in the workflow.

        Returns:
            dict: The generated questions.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        if chunks is None or len(chunks) != 3:
            raise ValueError("The input documents must be a list of 3 strings.")

        builder = WorkflowBuilder(document_1=chunks[0], document_2=chunks[1], document_3=chunks[2])

        builder.set_max_time(60)
        builder.set_max_steps(5)
        builder.set_max_tokens(500)

        # Step A: QuestionGeneration
        builder.generative_step(
            id="question_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Push.new("questions")],
        )

        flow = [
            Edge(
                source="question_generation",
                target="_end",
            )
        ]
        builder.flow(flow)
        builder.set_return_value("questions")
        workflow = builder.build()

        return workflow

    def parse_result(self, result: List[TaskResult]):

        results = []
        for r in result:
            onehop = get_text_between_tags(r.result, "1hop")
            twohop = get_text_between_tags(r.result, "2hop")
            threehop = get_text_between_tags(r.result, "3hop")
            answer = get_text_between_tags(r.result, "answer")
            results.append(
                {
                    "1-hop": onehop,
                    "2-hop": twohop,
                    "3-hop": threehop,
                    "answer": answer,
                    "model": r.model,
                }
            )
        return results
