import json
import logging
from typing import List

from dria.models import TaskInput
from dria.pipelines import Step, StepTemplate
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Edge,
    Size,
    Expression,
    ConditionBuilder,
    GetAll,
    Workflow,
    Push,
    Read,
)

from dria.factory.qa_pipeline.utils import get_text_between_tags
from dria.factory.utilities import get_abs_path


class QuestionStep(StepTemplate):

    def create_workflow(
        self,
        chunk: str,
        backstory: str,
    ) -> Workflow:
        """Generate questions for a given context and backstory.

        Args:
            chunk (str): The input data to be used in the workflow.
            backstory (str): The input data to be used in the workflow.
            max_time (int, optional): The maximum time to run the workflow. Defaults to 300.
            max_steps (int, optional): The maximum number of steps to run the workflow. Defaults to 30.
            max_tokens (int, optional): The maximum number of tokens to use in the workflow. Defaults to 750.

        Returns:
            dict: The generated questions.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        builder = WorkflowBuilder(backstory=backstory, context=chunk)

        builder.set_max_time(self.config.max_time)
        builder.set_max_steps(self.config.max_steps)
        builder.set_max_tokens(self.config.max_tokens)

        # Step A: QuestionGeneration
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
        workflow = builder.build()

        return workflow

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the question generation step.

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            TaskInput: A TaskInput object for the answer generation step.

        Raises:
            ValueError: If no valid question is generated.
        """
        inputs = []
        for questions in step.output:
            if questions.result == "":
                continue
            q_round = json.loads(questions.result)
            for q in q_round:
                question = get_text_between_tags(q, "generated_question")
                if question is None:
                    continue

                inputs.append(
                    TaskInput(
                        context=questions.task_input["context"],
                        persona=self.params.persona,
                        question=question.strip(),
                    )
                )
        return inputs
