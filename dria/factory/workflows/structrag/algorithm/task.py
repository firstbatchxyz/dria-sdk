from typing import List
from dria.models import TaskResult
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class StructRAGAlgorithm(SingletonTemplate):

    def workflow(
        self,
        documents: List[str],
        query: str,
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param documents: The documents to be used for the StructRAG algorithm.
        :param query: The query to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            documents=documents,
            query=query
        )
        self.params.documents = documents
        self.params.query = query
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
        return [
            {
                "algorithm": r.result.strip(),
                "query": self.params.query,
                "documents": self.params.documents,
            }
            for r in result
        ]
