from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path, parse_json, get_tags
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class ExtendedListOutput(BaseModel):
    extended_list: List[str] = Field(..., description="Extended list of items")
    model: str = Field(..., description="Model used for generation")


class ListExtender(SingletonTemplate):
    # Input fields
    e_list: List[str] = Field(..., description="Initial list to be extended")

    # Output schema
    OutputSchema = ExtendedListOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for extending a list.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(e_list=self.e_list)

        # Define the generation step
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("extended_list")],
        )

        # Define the flow
        flow = [
            Edge(source="0", target="_end"),
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("extended_list")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[ExtendedListOutput]:
        """
        Parse the results into validated ExtendedListOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[ExtendedListOutput]: List of validated extended list outputs
        """
        outputs = []
        for r in result:
            new_list = parse_json(
                get_tags(r.result, "extended_list")[0]
                .replace("\n", "")
                .replace("'", '"')
            )
            # Combine the new list with the original list
            combined_list = list(set(new_list + self.e_list))
            outputs.append(
                ExtendedListOutput(extended_list=combined_list, model=r.model)
            )
        return outputs
