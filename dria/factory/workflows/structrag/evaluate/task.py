from typing import List
from dria.models import TaskResult
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class StructRAGDecompose(SingletonTemplate):

    def workflow(
        self,
        knowledge_info: str,
        query: str,
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param knowledge_info: The documents to be used for the StructRAG algorithm.
        :param query: The query to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            knowledge_info=knowledge_info,
            query=query
        )
        self.params.knowledge_info = knowledge_info
        self.params.query = query
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("decompose.md"),
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
                "table": r.result.strip(),
                "query": self.params.query,
                "knowledge_info": self.params.knowledge_info,
            }
            for r in result
        ]


class StructRAGExtract(SingletonTemplate):

    def workflow(
        self,
        sub_question: str,
        structured_knowledge: str,
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param sub_question: The documents to be used for the StructRAG algorithm.
        :param structured_knowledge: The query to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            sub_question=sub_question,
            knowledge=structured_knowledge
        )
        self.params.sub_question = sub_question
        self.params.structured_knowledge = structured_knowledge
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("extract.md"),
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
                "precise_knowledge": r.result.strip(),
                "sub_question": self.params.sub_question,
                "structured_knowledge": self.params.structured_knowledge,
            }
            for r in result
        ]


class StructRAGAnswer(SingletonTemplate):

    def workflow(
        self,
        question: str,
        sub_questions: List[str],
        precise_knowledge: List[str],
    ) -> Workflow:
        """
        https://arxiv.org/pdf/2410.08815
        Generate StructRAG Algorithm

        :param question: The documents to be used for the StructRAG algorithm.
        :param sub_questions: The documents to be used for the StructRAG algorithm.
        :param precise_knowledge: The query to be used for the StructRAG algorithm.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            question=question,
            sub_questions=sub_questions,
            precise_knowledge=precise_knowledge
        )
        self.params.question = question
        self.params.sub_questions = sub_questions
        self.params.precise_knowledge = precise_knowledge
        builder.set_max_tokens(1000)
        # Add a generative step using the prompt string
        builder.generative_step(
            path=get_abs_path("extract.md"),
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
                "table": r.result.strip(),
                "query": self.params.query,
                "documents": self.params.documents,
            }
            for r in result
        ]