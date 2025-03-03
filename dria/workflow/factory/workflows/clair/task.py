from typing import List
from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
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


class Clair(WorkflowTemplate):
    """
    Clair is a task that takes a student solution and reasoning and corrects the student solution.
    """

    # Output schema
    OutputSchema = ClairOutput

    def define_workflow(self):
        """
        Creates a workflow for correcting student solutions.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables

        self.add_step(prompt=get_abs_path("prompt.md"), outputs=["response"])
        self.set_output("response")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated ClairOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated outputs
        """
        pattern = r"\{teacher_reasoning\}(.*?)\{corrected_student_solution\}(.*)"

        outputs = []
        for r in result:
            match = re.search(pattern, r.result, re.DOTALL)
            if not match:
                raise ValueError(f"Invalid result format: {r.result}")

            teacher_reasoning = match.group(1).strip()
            corrected_student_solution = match.group(2).strip()

            output = self.OutputSchema(
                reasoning=teacher_reasoning,
                corrected_student_solution=corrected_student_solution,
                task=r.task_input["task"],
                student_solution=r.task_input["student_solution"],
                model=r.model,
            )
            outputs.append(output)

        return outputs
