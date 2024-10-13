from typing import Union, List, Dict, Any
from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
import re


class Clair(SingletonTemplate):
    """
    Clair is a task that takes a student solution and reasoning and corrects the student solution.
    """

    def workflow(self, task: str, student_solution: str) -> Workflow:

        self.params.task = task
        self.params.student_solution = student_solution

        builder = WorkflowBuilder(task=task, student_solution=student_solution)
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("response")],
        )
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("response")
        return builder.build()

    def parse_result(self, result: List[TaskResult]) -> List[Dict[str, str]]:
        """Parse the result from TaskResult objects and extract the reasoning and corrected student solution.

        Args:
            result (List[TaskResult]): A list of TaskResult objects.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing the parsed information.
        """
        results = []
        pattern = r"\{teacher_reasoning\}(.*?)\{corrected_student_solution\}(.*)"

        for r in result:
            _result = r.result
            model = r.model

            # Use regex to extract teacher reasoning and corrected student solution
            match = re.search(pattern, _result, re.DOTALL)
            if match:
                teacher_reasoning = match.group(1).strip()
                corrected_student_solution = match.group(2).strip()
            else:
                raise ValueError(f"Invalid result format: {_result}")

            results.append(
                {
                    "reasoning": teacher_reasoning,
                    "corrected_student_solution": corrected_student_solution,
                    "task": self.params.task,
                    "student_solution": self.params.student_solution,
                    "model": model,
                }
            )
        return results
