from dria.models import TaskInput
from dria.factory.utilities import get_abs_path, extract_backtick_label
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    GetAll,
    Workflow,
)
import logging
from typing import List
from dria.pipelines import Step, StepTemplate

logger = logging.getLogger(__name__)


class ReviseAtomicFact(StepTemplate):
    def create_workflow(
            self, atomic_fact: str, response: str, question: str, **kwargs
    ) -> Workflow:
        """Revise atomic facts.

        Args:
            :param atomic_fact: The atomic fact to be revised.
            :param response: The response atomic fact extracted from.
            :param question: The question for the response.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(atomic_fact=atomic_fact, response=response)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: GenerateBackstory
        builder.generative_step(
            id="revise",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("revised_fact")],
        )

        flow = [Edge(source="revise", target="_end")]
        builder.flow(flow)
        builder.set_return_value("revised_fact")
        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the revision

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            List[TaskInput]: A list of TaskInput objects for the next step.

        Raises:
            Exception: If there's an error processing the step output.
        """

        try:
            tasks = []
            for i,s in enumerate(step.output):
                input_params = step.input_params[s.id]
                try:
                    tasks.append(TaskInput(
                        revised_fact=extract_backtick_label(s.result, "")[0],
                        fact=input_params.atomic_fact,
                        response=input_params.response,
                        question=input_params.question,
                    ))
                except Exception as e:
                    pass
            return tasks
        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise
