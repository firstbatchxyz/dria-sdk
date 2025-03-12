import json
from typing import List

from dria_workflows import (
    Workflow,
)
from pydantic import BaseModel, Field

from dria.models import TaskResult
from dria.workflow import WorkflowTemplate
from dria.workflow.factory.utilities import get_abs_path, parse_json


class GraphRelation(BaseModel):
    node_1: str = Field(..., description="A concept from extracted ontology")
    node_2: str = Field(..., description="A related concept from extracted ontology")
    edge: str = Field(..., description="Relationship between the two concepts")


class GraphOutput(BaseModel):
    graph: GraphRelation = Field(..., description="The generated graph relation")
    model: str = Field(..., description="Model used for generation")


class GenerateGraph(WorkflowTemplate):
    # Output schema
    OutputSchema = GraphOutput

    def define_workflow(self) -> None:
        """
        Generate a Task to extract terms and their relations from the given context.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        self.add_step(prompt=get_abs_path("prompt.md"))

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated GraphOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated graph outputs
        """
        outputs = []
        for r in result:
            try:
                graph_data = parse_json(r.result.strip())
                for g in graph_data:
                    graph_relation = GraphRelation(**g)
                    outputs.append(
                        self.OutputSchema(graph=graph_relation, model=r.model)
                    )
            except json.JSONDecodeError:
                # Handle the case where the result is not valid JSON
                graph_data = r.result.strip()
                # You might want to add proper error handling here
                continue

        return outputs
