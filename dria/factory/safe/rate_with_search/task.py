from dria.models import TaskInput
from dria.factory.utilities import get_abs_path, extract_backtick_label
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    GetAll,
    Push,
    Workflow,
    ConditionBuilder,
    Expression,
    Size,
)
import logging
from typing import List
from dria.pipelines import Step, StepTemplate

logger = logging.getLogger(__name__)

class NextSearch(StepTemplate):
    def create_workflow(self, query: str, atomic_fact:str, **kwargs) -> Workflow:
        """Revise atomic facts.

        Args:
            :param query: query to search for
            :param atomic_fact: atomic fact to use

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(query=query)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        builder.search_step(
            id="search",
            search_query="{{query}}",
            n_results=5,
            outputs=[Push.new("search_results")],
        )

        flow = [
            Edge(source="search", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("search_results")
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
            return [
                TaskInput(
                    atomic_fact=step.input[i].atomic_fact,
                    response=step.input[i].response,
                    question=step.input[i].question,
                    search_results=s.result,
                )
                for i, s in enumerate(step.output)
            ]
        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise


class NextQuery(StepTemplate):
    def create_workflow(self, atomic_fact: str, search_results: str, **kwargs) -> Workflow:
        """Revise atomic facts.

        Args:
            :param atomic_fact: The atomic fact to be revised.
            :param search_results: The search results to process.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(atomic_fact=atomic_fact, search_results=search_results)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        builder.generative_step(
            id="revise",
            path=get_abs_path("next_search.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("query")],
        )
        flow = [
            Edge(source="revise", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("query")
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
            return [
                TaskInput(
                    atomic_fact=s.task_input["atomic_fact"],
                    response=step.input[i].response,
                    question=step.input[i].question,
                    query=extract_backtick_label(s.result, "")[0]
                )
                for i, s in enumerate(step.output)
            ]
        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise


class RateWithSearch(StepTemplate):
    def create_workflow(
        self,
        atomic_fact: str,
        response: str,
        question: str,
        search_results: str,
        **kwargs,
    ) -> Workflow:
        """Revise atomic facts.

        Args:
            :param atomic_fact: The atomic fact to be revised.
            :param response: The response atomic fact extracted from.
            :param question: The question for the response.
            :param search_results: The search results for the response.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(
            atomic_fact=atomic_fact, search_results=search_results
        )
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: GenerateBackstory
        builder.generative_step(
            id="evaluate",
            path=get_abs_path("final_answer.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("result")],
        )

        flow = [Edge(source="evaluate", target="_end")]
        builder.flow(flow)
        builder.set_return_value("result")
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
        results = []  # a list of dicts
        try:
            for i, s in enumerate(step.output):
                if all(step.input[i].question not in d.values() for d in results):
                    results.append(
                        {
                            "question": step.input[i].question,
                            "response": step.input[i].response,
                            "facts": [],
                        }
                    )
                index = 0
                for ix, res in enumerate(results):
                    if res["question"] == step.input[i].question:
                        index = ix
                results[index]["facts"].append(
                    {
                        "fact": step.input[index].atomic_fact,
                        "supported": "[SUPPORTED]" in s.result,
                        "reason": s.result,
                    }
                )

        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise

        return [TaskInput(**r) for r in results]
