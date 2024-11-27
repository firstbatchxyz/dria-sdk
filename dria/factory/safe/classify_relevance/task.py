import json
import re
from dria.models import TaskInput
from dria.factory.utilities import get_abs_path
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
from typing import List, Union
from dria.pipelines import Step, StepTemplate

logger = logging.getLogger(__name__)


class ClassifyAtomicFacts(StepTemplate):
    def create_workflow(
        self, question: str, response: str, revised_fact: str
    ) -> Workflow:
        """
        Classify atomic facts whether they are relevant or not.

        Args:
            :param question: The question text.
            :param response: The response text.
            :param revised_fact: The revised atomic facts text.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(
            question=question, response=response, revised_fact=revised_fact
        )
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: GenerateBackstory
        builder.generative_step(
            id="classify",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("classification")],
        )

        flow = [Edge(source="classify", target="_end")]
        builder.flow(flow)
        builder.set_return_value("classification")
        return builder.build()

    def callback(self, step: "Step") -> Union[List[TaskInput], TaskInput]:
        tasks = []
        for i, s in enumerate(step.output):
            try:
                if "[Foo]" in s.result:
                    tasks.append(
                        TaskInput(
                            relevance="1",
                            atomic_fact=step.input[i].revised_fact,
                            response=step.input[i].response,
                            question=step.input[i].question,
                            search_results="N/A",
                        )
                    )
                elif "[Not Foo]" in s.result:
                    # TODO: Maybe don't create tasks for irrelevant facts
                    """tasks.append(
                        TaskInput(
                            relevance="0",
                            atomic_fact=step.input[i].revised_fact,
                            response=step.input[i].response,
                            question=step.input[i].question,
                            search_results="N/A"
                        )
                    )"""
                    pass
                else:
                    pass

            except Exception as e:
                logger.error(f"Error in atomic fact split: {str(e)}")
        return tasks
