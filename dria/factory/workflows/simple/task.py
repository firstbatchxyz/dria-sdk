from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.factory.workflows.template import SingletonTemplate


class Simple(SingletonTemplate):

    def workflow(self, prompt: str) -> Workflow:
        builder = WorkflowBuilder()
        builder.generative_step(
            prompt=prompt, operator=Operator.GENERATION, outputs=[Write.new("response")]
        )
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("response")
        return builder.build()

    def parse_result(self, result):
        return result[0]
