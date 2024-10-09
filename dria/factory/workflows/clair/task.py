from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.factory.utilities import get_abs_path


def clair(task: str, student_solution: str) -> Workflow:
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
