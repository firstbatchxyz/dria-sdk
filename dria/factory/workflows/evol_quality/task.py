from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.utilities import get_abs_path
from dria.models import TaskResult
from dria.factory.workflows.template import SingletonTemplate
from typing import Dict, List
from pydantic import BaseModel, Field

MUTATION_TEMPLATES: Dict[str, str] = {
    "HELPFULNESS": "Please make the Response more helpful to the user.",
    "RELEVANCE": "Please make the Response more relevant to #Given Prompt#.",
    "DEEPENING": "Please make the Response more in-depth.",
    "CREATIVITY": "Please increase the creativity of the response.",
    "DETAILS": "Please increase the detail level of Response.",
}


class Output(BaseModel):
    response: str = Field(..., description="Original response")
    evolved_response: str = Field(..., description="Evolved/rewritten response")
    method: str = Field(..., description="Method used for evolution")
    model: str = Field(..., description="Model used for generation")


class EvolveQuality(SingletonTemplate):

    prompt: str
    response: str
    method: str
    OutputSchema = Output

    def workflow(self) -> Workflow:

        builder = WorkflowBuilder(
            prompt=self.prompt, response=self.response, method=self.method
        )
        builder.generative_step(
            path=get_abs_path("rewrite.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("rewritten_response")],
        )
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("rewritten_response")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[Output]:
        """
        Process multiple results and return as list of Output schemas
        Args:
            result: List of TaskResult objects
        Returns:
            List[Output]: List of validated output objects
        """
        return [
            Output(
                response=self.response,
                evolved_response=r.result.strip(),
                method=self.method,
                model=r.model,
            )
            for r in result
        ]
