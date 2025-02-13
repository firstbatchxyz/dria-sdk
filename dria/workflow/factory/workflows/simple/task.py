from typing import List
from pydantic import BaseModel, Field
from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.workflow import WorkflowTemplate
from dria.models import TaskResult


class SimpleOutput(BaseModel):
    prompt: str = Field(..., description="The prompt used to generate text.")
    generation: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")


class Simple(WorkflowTemplate):
    # Input fields
    prompt: str = Field(..., description="Input prompt for generation")

    # Output schema
    OutputSchema = SimpleOutput

    def build(self) -> Workflow:
        """
        Creates a workflow for simple text generation.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(prompt=self.prompt)
        builder.set_max_tokens(self.params.max_tokens)  # TODO: more builtin stuff
        builder.set_max_steps(self.params.max_steps)
        builder.set_max_time(self.params.max_time)

        builder.generative_step(
            prompt="{{prompt}}",
            operator=Operator.GENERATION,
            outputs=[Write.new("response")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        builder.set_return_value("response")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated SimpleOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SimpleOutput]: List of validated simple outputs
        """
        return [
            self.OutputSchema(
                prompt=self.prompt, generation=res.result, model=res.model
            )
            for res in result
        ]
