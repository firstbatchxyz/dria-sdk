import json
from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path, parse_json
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class GraphRelation(BaseModel):
    node_1: str = Field(..., description="A concept from extracted ontology")
    node_2: str = Field(..., description="A related concept from extracted ontology")
    edge: str = Field(..., description="Relationship between the two concepts")


class GraphOutput(BaseModel):
    graph: GraphRelation = Field(..., description="The generated graph relation")
    model: str = Field(..., description="Model used for generation")


class GenerateGraph(SingletonTemplate):
    # Input fields
    context: str = Field(
        ..., description="The context from which to extract the ontology of terms"
    )

    # Output schema
    OutputSchema = GraphOutput

    def workflow(self) -> Workflow:
        """
        Generate a Task to extract terms and their relations from the given context.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(context=self.context)
        builder.set_max_tokens(750)
        builder.set_max_time(75)

        # Add a generative step using the prompt
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("graph")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("graph")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[GraphOutput]:
        """
        Parse the results into validated GraphOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[GraphOutput]: List of validated graph outputs
        """
        outputs = []
        for r in result:
            try:
                graph_data = parse_json(r.result.strip())
                for g in graph_data:
                    graph_relation = GraphRelation(**g)
                    outputs.append(GraphOutput(graph=graph_relation, model=r.model))
            except json.JSONDecodeError:
                # Handle the case where the result is not valid JSON
                graph_data = r.result.strip()
                # You might want to add proper error handling here
                continue

        return outputs
