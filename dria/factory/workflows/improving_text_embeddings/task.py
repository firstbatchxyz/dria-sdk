from typing import Any, List, Dict
import json
from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from .utils import parse_json
from pydantic import BaseModel, Field


class SemanticUnit(BaseModel):
    S1: str = Field(..., description="First semantic unit")
    S2: str = Field(..., description="Second semantic unit with high similarity to S1")
    S3: str = Field(..., description="Third semantic unit with low similarity to S1")


class SemanticTripletOutput(BaseModel):
    triplet: SemanticUnit = Field(..., description="The semantic triplet units")
    model: str = Field(..., description="Model used for generation")


class SemanticTriplet(SingletonTemplate):
    """
    SemanticTripletOutput
    """

    # Input fields
    unit: str = Field(
        ..., description="The textual unit type (e.g., sentence, paragraph)"
    )
    language: str = Field(..., description="The language for generation")
    high_score: int = Field(
        ..., description="Similarity score between S1 and S2 (1 to 5)"
    )
    low_score: int = Field(
        ..., description="Similarity score between S1 and S3 (1 to 5)"
    )
    difficulty: str = Field(
        ..., description="Education level required to understand the units"
    )

    # Output schema
    OutputSchema = SemanticTripletOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating semantic triplets.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(
            unit=self.unit,
            language=self.language,
            high_score=str(self.high_score),
            low_score=str(self.low_score),
            difficulty=self.difficulty,
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

    @staticmethod
    def callback(result: List[TaskResult]) -> List[SemanticTripletOutput]:
        """
        Parse the results into validated SemanticTripletOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SemanticTripletOutput]: List of validated semantic triplet outputs
        """
        return [
            SemanticTripletOutput(
                triplet=SemanticUnit(**parse_json(r.result)), model=r.model
            )
            for r in result
        ]


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
        builder.set_max_tokens(500)
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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, Any]]:
        results = []
        for r in result:
            output = parse_json(r.result)
            output["model"] = r.model
            results.append(output)
        return results


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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, Any]]:
        results = []
        for r in result:
            output = parse_json(r.result)
            output["model"] = r.model
            results.append(output)
        return results


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
        builder.set_max_tokens(750)
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

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, Any]]:
        results = []
        for r in result:
            output = parse_json(r.result)
            output["model"] = r.model
            results.append(output)
        return results
