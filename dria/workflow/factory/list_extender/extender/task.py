from typing import List

from pydantic import BaseModel, Field

from dria.models import TaskResult
from dria.workflow.factory.utilities import get_abs_path, parse_json, get_tags
from dria.workflow.template import WorkflowTemplate


class ExtendedListOutput(BaseModel):
    extended_list: List[str] = Field(..., description="Extended list of items")
    model: str = Field(..., description="Model used for generation")


class ListExtender(WorkflowTemplate):
    # Output schema
    OutputSchema = ExtendedListOutput
    max_time = 300
    max_steps = 20
    max_tokens = 750

    def define_workflow(self) -> None:
        # Single generation step that extends the list
        self.add_step(prompt=get_abs_path("prompt.md"))

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated ExtendedListOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated extended list outputs
        """
        outputs = []
        for r in result:
            new_list = parse_json(
                get_tags(r.result, "extended_list")[0]
                .replace("\n", "")
                .replace("'", '"')
            )
            # Combine the new list with the original list
            combined_list = list(set(new_list + r.inputs["e_list"]))
            outputs.append(
                self.OutputSchema(extended_list=combined_list, model=r.model)
            )
        return outputs
