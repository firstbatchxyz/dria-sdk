from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.workflow.factory.utilities import get_abs_path
from dria.models import TaskResult
from dria.workflow import WorkflowTemplate
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


class EvolveQuality(WorkflowTemplate):
    OutputSchema = Output

    def define_workflow(self):
       self.add_step(get_abs_path("rewrite.md"))

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Process multiple results and return as list of Output schemas
        Args:
            result: List of TaskResult objects
        Returns:
            List[OutputSchema]: List of validated output objects
        """
        return [
            self.OutputSchema(
                response=r.inputs["response"],
                evolved_response=r.result.strip(),
                method=r.inputs["method"],
                model=r.model,
            )
            for r in result
        ]
