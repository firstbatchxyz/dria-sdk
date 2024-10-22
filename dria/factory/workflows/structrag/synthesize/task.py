from typing import List
from dria.models import TaskResult
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from .utils import extract_solution_order
import re


class StructRAGSynthesize(SingletonTemplate):

    def workflow(
        self,
        seed: str
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(topic=seed)
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("output")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("output")
        return builder.build()

    def parse_result(self, result: List[TaskResult]):
        output = []
        for r in result:
            matches = re.findall(r'DOCUMENTS_INFO:\n(.+)\nQUERY:\n(.+?)\n', r.result)
            output.append([
                {
                    'documents_info': [doc.strip('"') for doc in docs.split(', ')],
                    'query': query.strip()
                }
                for docs, query in matches
            ])
        return output


class StructRAGSimulate(SingletonTemplate):

    def workflow(
        self,
        query: str
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param query: The query to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(query=query)
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("simulate.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("output")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("output")
        return builder.build()

    def parse_result(self, result: List[TaskResult]):
        return [
            {
                "solutions": r.result.strip(),
            }
            for r in result
        ]


class StructRAGJudge(SingletonTemplate):

    def workflow(
        self,
        query: str,
        documents_info: List[str],
        solutions: str
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param query: The query to be used for the StructRAG algorithm.
        :param documents_info: The documents to be used for the StructRAG algorithm.
        :param solutions: The solutions to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(query=query, documents_info=documents_info, solutions=solutions)
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("judge.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("output")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("output")
        return builder.build()

    def parse_result(self, result: List[TaskResult]):
        return [
            {
                "simulation": r.result.strip(),
                "order": extract_solution_order(r.result.strip())
            }
            for r in result
        ]