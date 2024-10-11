from typing import Any
import json
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class SemanticTriplet(SingletonTemplate):

    def workflow(
        self,
        unit: str,
        language: str,
        high_score: int,
        low_score: int,
        difficulty: str,
    ) -> Workflow:
        """
        Generate a Task to create a JSON object with three units (S1, S2, S3) having specified semantic similarity scores.

        :param unit: The textual unit (e.g., "sentence", "paragraph") to be generated.
        :param language: The language in which the units should be written.
        :param high_score: The similarity score between S1 and S2 (1 to 5).
        :param low_score: The similarity score between S1 and S3 (1 to 5).
        :param difficulty: The education level required to understand the units (e.g., "college", "high school").
        :return: A Task object representing the workflow.
        """

        builder = WorkflowBuilder(
            unit=unit,
            language=language,
            high_score=str(high_score),
            low_score=str(low_score),
            difficulty=difficulty,
        )
        builder.generative_step(
            path=get_abs_path("monolingual_triplet.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("semantic_triple")],
        )
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("semantic_triple")
        return builder.build()

    def parse_result(self, result: Any):
        return json.loads(result[0].strip())


class TextMatching(SingletonTemplate):

    def workflow(
        self,
        task_description: str,
        language: str,
    ) -> Workflow:
        """
        Generate a Task to create a JSON object with 'input' and 'positive_document' for a specified text matching task.

        :param task_description: The description of the text matching task.
        :param language: The language in which the texts should be written.
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(task=task_description, language=language)

        # Add a generative step using the prompt stored in 'text_matching_example.md'
        builder.generative_step(
            path=get_abs_path(
                "long_text_matching.md"
            ),  # The prompt file containing the provided prompt
            operator=Operator.GENERATION,
            outputs=[Write.new("text_matching_example")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("text_matching_example")
        return builder.build()

    def parse_result(self, result: Any):
        return json.loads(result[0])


class TextClassification(SingletonTemplate):

    def workflow(
        self, task_description: str, language: str, clarity: str, difficulty: str
    ) -> Workflow:
        """
        Generate a Task to create a JSON object with 'input_text', 'label', and 'misleading_label' for a specified text classification task.

        :param task_description: The description of the text classification task.
        :param language: The language in which the texts should be written.
        :param clarity: The clarity of the input text (e.g., "clear", "ambiguous").
        :param difficulty: The education level required to understand the input text (e.g., "college", "high school").
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            task=task_description,
            language=language,
            clarity=clarity,
            difficulty=difficulty,
        )

        # Add a generative step using the prompt stored in 'text_classification_example.md'
        builder.generative_step(
            path=get_abs_path("text_classification.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("classification_example")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("classification_example")
        return builder.build()

    def parse_result(self, result: Any):
        return json.loads(result[0])


class TextRetrieval(SingletonTemplate):

    def workflow(
        self,
        task_description: str,
        query_type: str,
        query_length: str,
        clarity: str,
        num_words: int,
        language: str,
        difficulty: str,
    ) -> Workflow:
        """
        Generate a Task to create a JSON object with 'user_query', 'positive_document', and 'hard_negative_document' for a specified retrieval task.

        :param task_description: The description of the retrieval task.
        :param query_type: The type of the user query (e.g., "informational", "navigational").
        :param query_length: The length of the user query (e.g., "short", "long").
        :param clarity: The clarity of the user query (e.g., "clear", "ambiguous").
        :param num_words: The minimum number of words for the documents.
        :param language: The language in which the query and documents should be written.
        :param difficulty: The education level required to understand the query and documents (e.g., "college", "high school").
        :return: A Task object representing the workflow.
        """

        # Initialize the workflow with variables to be used in the prompt
        builder = WorkflowBuilder(
            task=task_description,
            query_type=query_type,
            query_length=query_length,
            clarity=clarity,
            num_words=str(num_words),
            language=language,
            difficulty=difficulty,
        )

        # Add a generative step using the prompt stored in 'text_retrieval_example.md'
        builder.generative_step(
            path=get_abs_path("text_retrieval.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("retrieval_example")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("retrieval_example")
        return builder.build()

    def parse_result(self, result: Any):
        return json.loads(result[0])
