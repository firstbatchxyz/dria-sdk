import json
from json import JSONDecodeError

from dria.models import TaskInput
from dria.factory.utilities import parse_json, get_abs_path, extract_backtick_label
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Workflow,
)
import logging
from typing import List
from dria.pipelines import Step, StepTemplate

logger = logging.getLogger(__name__)


class NextSearch(StepTemplate):
    def create_workflow(self, query: str, atomic_fact: str, **kwargs) -> Workflow:
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
            outputs=[Write.new("search_results")],
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
            tasks = []
            for i,s in enumerate(step.output):
                input_params = step.input_params[s.id]
                try:
                    parsed_ = parse_json(s.result)["organic"]
                    parsed_ = [json.dumps(x) for x in parsed_]
                    if input_params.search_results[0] == "N/A":
                        combined_ = input_params.search_results[1:] + parsed_
                    else:
                        combined_ = input_params.search_results + parsed_
                except Exception as e:
                    combined_ = input_params.search_results + s.result
                if not combined_:
                    continue
                tasks.append(
                    TaskInput(
                        atomic_fact=input_params.atomic_fact,
                        response=input_params.response,
                        question=input_params.question,
                        search_results=combined_,
                    )
                )
            return tasks
        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise


class NextQuery(StepTemplate):
    def create_workflow(
            self, atomic_fact: str, search_results: List[str], **kwargs
    ) -> Workflow:
        """Revise atomic facts.

        Args:
            :param atomic_fact: The atomic fact to be revised.
            :param search_results: The search results to process.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(
            atomic_fact=atomic_fact, search_results=search_results
        )
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
            tasks = []
            for i,s in enumerate(step.output):
                try:
                    input_params = step.input_params[s.id]
                    query = self.clean_query(extract_backtick_label(s.result, "")[0])
                    if query.split("site:jina.ai")[0] == "":
                        continue
                    tasks.append(
                        TaskInput(
                            atomic_fact=input_params.atomic_fact,
                            response=input_params.response,
                            question=input_params.question,
                            query=query,
                            search_results=input_params.search_results,
                        )
                    )
                except Exception as e:
                    pass
            return tasks

        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise

    @staticmethod
    def clean_query(query: str) -> str:
        """
        Clean a search query by removing formatting prefixes and unnecessary quotes.

        Args:
            query: The raw query string

        Returns:
            A cleaned query string ready for search
        """
        # Remove any whitespace from ends
        cleaned = query.strip()

        # Remove formatting prefixes if they exist
        prefixes = ["plaintext\n", "markdown\n"]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]

        # Remove surrounding quotes if they exist
        cleaned = cleaned.replace('"', "")

        return cleaned


class RateWithSearch(StepTemplate):
    def create_workflow(
            self,
            atomic_fact: str,
            response: str,
            question: str,
            search_results: List[str],
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
                input_params = step.input_params[s.id]
                if all(input_params.question not in d.values() for d in results):
                    results.append(
                        {
                            "question": input_params.question,
                            "response": input_params.response,
                            "facts": [],
                        }
                    )
                index = 0
                for ix, res in enumerate(results):
                    if res["question"] == input_params.question:
                        index = ix
                try:
                    results[index]["facts"].append(
                        {
                            "fact": input_params.atomic_fact,
                            "links": parse_json(input_params.search_results),
                            "supported": "[SUPPORTED]" in s.result,
                        }
                    )
                except JSONDecodeError:
                    results[index]["facts"].append(
                        {
                            "fact": input_params.atomic_fact,
                            "links": input_params.search_results,
                            "supported": "[SUPPORTED]" in s.result,
                        }
                    )


        except Exception as e:
            logger.error(f"Error in atomic fact revision: {str(e)}")
            raise

        return [TaskInput(**r) for r in results]
