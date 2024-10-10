from typing import Union, List, Dict
from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


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

    def parse_result(self, result: Union[str, List[str]]) -> Dict[str, str]:

        # if result is a list, take first element
        if isinstance(result, list):
            result = result[0]

        parts = result.split("{corrected_student_solution}")
        if len(parts) == 2:
            teacher_reasoning = parts[0].replace("{teacher_reasoning}", "").strip()
            # The second part is the corrected_student_solution
            corrected_student_solution = parts[1].strip()
        else:
            raise ValueError(f"Invalid result format: {result}")

        return {
            "reasoning": teacher_reasoning,
            "corrected_student_solution": corrected_student_solution,
            "task": self.params.task,
            "student_solution": self.params.student_solution,
        }
