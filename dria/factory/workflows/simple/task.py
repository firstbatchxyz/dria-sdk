from typing import List
from pydantic import BaseModel, Field
from dria_workflows import Workflow, WorkflowBuilder, Operator, Edge, Write
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class SimpleOutput(BaseModel):
    prompt: str = Field(..., description="The prompt used to generate text.")
    generation: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")


class Simple(SingletonTemplate):
    # Input fields
    prompt: str = Field(..., description="Input prompt for generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens for generation")

    # Output schema
    OutputSchema = SimpleOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for simple text generation.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder()
        builder.set_max_tokens(self.max_tokens)

        builder.generative_step(
            prompt=self.prompt,
            operator=Operator.GENERATION,
            outputs=[Write.new("response")]
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        builder.set_return_value("response")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[SimpleOutput]:
        """
        Parse the results into validated SimpleOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SimpleOutput]: List of validated simple outputs
        """
        return [
            SimpleOutput(
                prompt=self.prompt,
                generation=res.result,
                model=res.model
            )
            for res in result
        ]