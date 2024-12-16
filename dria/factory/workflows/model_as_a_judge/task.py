from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class ValidationOutput(BaseModel):
    prediction: str = Field(..., description="The prediction result.")
    correct_answer: str = Field(..., description="The correct answer.")
    validation: bool = Field(..., description="Validation result (True/False)")
    model: str = Field(..., description="Model used for validation")


class EvaluationOutput(BaseModel):
    question: str = Field(..., description="Question used for evaluation")
    prediction: str = Field(..., description="Prediction result (True/False)")
    evaluation: str = Field(..., description="Evaluation result")
    model: str = Field(..., description="Model used for evaluation")


class ValidatePrediction(SingletonTemplate):
    # Input fields
    prediction: str = Field(..., description="The predicted answer to be evaluated")
    correct_answer: str = Field(
        ..., description="The correct answer to compare against"
    )

    # Output schema
    OutputSchema = ValidationOutput

    def workflow(self) -> Workflow:
        """
        Generate a Task to determine if the predicted answer is contextually and semantically correct.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            prediction=self.prediction, correct_answer=self.correct_answer
        )

        # Add a generative step using the prompt
        builder.generative_step(
            path=get_abs_path("validate.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("validation_result")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("validation_result")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[ValidationOutput]:
        """
        Parse the results into validated ValidationOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[ValidationOutput]: List of validated outputs
        """
        outputs = []
        for r in result:
            if r.result.lower() == "true":
                outputs.append(
                    ValidationOutput(
                        prediction=self.prediction,
                        correct_answer=self.correct_answer,
                        validation=True,
                        model=r.model,
                    )
                )
            elif r.result.lower() == "false":
                outputs.append(
                    ValidationOutput(
                        prediction=self.prediction,
                        correct_answer=self.correct_answer,
                        validation=False,
                        model=r.model,
                    )
                )
            else:
                raise ValueError("The result is not a boolean value.")
        return outputs


class EvaluatePrediction(SingletonTemplate):
    # Input fields
    prediction: str = Field(..., description="The predicted answer to be evaluated")
    question: str = Field(..., description="The question to compare against")
    context: str = Field(..., description="The context to compare against")

    # Output schema
    OutputSchema = EvaluationOutput

    def workflow(self) -> Workflow:
        """
        Generate a Task to determine if the predicted answer is contextually and semantically correct.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            prediction=self.prediction, question=self.question, context=self.context
        )

        # Add a generative step using the prompt
        builder.generative_step(
            path=get_abs_path("evaluate.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("evaluation_result")],
        )

        # Define the flow of the workflow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("evaluation_result")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[EvaluationOutput]:
        """
        Parse the results into validated EvaluationOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[EvaluationOutput]: List of validated outputs
        """
        return [
            EvaluationOutput(
                question=self.question,
                prediction=self.prediction,
                evaluation=r.result,
                model=r.model,
            )
            for r in result
        ]
