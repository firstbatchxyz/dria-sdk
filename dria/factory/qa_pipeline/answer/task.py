import logging
from typing import List

from dria.models import TaskInput
from dria.pipelines import StepTemplate, Step
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Workflow, Read

from dria.factory.qa_pipeline.utils import (
    get_text_between_tags,
    remove_text_between_tags,
)
from dria.factory.utilities import get_abs_path


class AnswerStep(StepTemplate):
    def create_workflow(
        self,
        context: str,
        question: str,
        persona: str,
    ) -> Workflow:
        """Generate an answer to a question based on provided context while adopting a specific persona.

        Args:
            max_time (int, optional): The maximum time to run the workflow. Defaults to 300.
            max_steps (int, optional): The maximum number of steps to run the workflow. Defaults to 30.
            max_tokens (int, optional): The maximum number of tokens to run the workflow. Defaults to 750.

        Returns:
            dict: The output data from the workflow.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        builder = WorkflowBuilder(context=context, question=question, persona=persona)
        builder.set_max_time(self.config.max_time)
        builder.set_max_steps(self.config.max_steps)
        builder.set_max_tokens(self.config.max_tokens)

        # Step A: Answer Generation
        builder.generative_step(
            id="answer_generation",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="context", required=True),
                Read.new(key="question", required=True),
                Read.new(key="persona", required=True),
            ],
            outputs=[Write.new("answer")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="answer_generation", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("answer")

        # Build the workflow
        workflow = builder.build()

        return workflow

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the answer generation step.

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            Dict[str, str]: A dictionary containing the question and answer.

        Raises:
            ValueError: If no valid answer is generated.
        """
        returns = []
        for a in step.output:
            answer = get_text_between_tags(a.result, "answer")
            entry = remove_text_between_tags(answer, "rationale")

            if entry is None:
                continue

            returns.append(
                TaskInput(question=a.task_input["question"], answer=entry.strip())
            )
        return returns
