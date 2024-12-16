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
import re


class ClairOutput(BaseModel):
    reasoning: str = Field(..., description="Teacher's reasoning for corrections")
    corrected_student_solution: str = Field(
        ..., description="Corrected version of the student solution"
    )
    task: str = Field(..., description="Original task")
    student_solution: str = Field(..., description="Original student solution")
    model: str = Field(..., description="Model used for generation")


class Clair(SingletonTemplate):
    """
    Clair is a task that takes a student solution and reasoning and corrects the student solution.
    """

    # Input fields
    task: str = Field(..., description="The original task")
    student_solution: str = Field(
        ..., description="The student's solution to be corrected"
    )

    # Output schema
    OutputSchema = ClairOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for correcting student solutions.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            task=self.task, student_solution=self.student_solution
        )

        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("response")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("response")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[ClairOutput]:
        """
        Parse the results into validated ClairOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[ClairOutput]: List of validated outputs
        """
        pattern = r"\{teacher_reasoning\}(.*?)\{corrected_student_solution\}(.*)"

        outputs = []
        for r in result:
            match = re.search(pattern, r.result, re.DOTALL)
            if not match:
                raise ValueError(f"Invalid result format: {r.result}")

            teacher_reasoning = match.group(1).strip()
            corrected_student_solution = match.group(2).strip()

            output = ClairOutput(
                reasoning=teacher_reasoning,
                corrected_student_solution=corrected_student_solution,
                task=self.task,
                student_solution=self.student_solution,
                model=r.model,
            )
            outputs.append(output)

        return outputs
