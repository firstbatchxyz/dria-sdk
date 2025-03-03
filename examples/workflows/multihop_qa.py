import asyncio
from typing import List

from dria_workflows import WorkflowBuilder, Operator, Write, Edge, Read
from pydantic import BaseModel, Field

from dria import Model, Dria, WorkflowTemplate
from dria.models import TaskResult

dria = Dria()


class SimpleClass(BaseModel):
    output: str = Field(...)


class SimpleWorkflow(WorkflowTemplate):
    first_prompt: str
    second_prompt: str

    OutputSchema = SimpleClass

    def build(self):
        builder = WorkflowBuilder(
            {"first_prompt": self.first_prompt, "second_prompt": self.second_prompt}
        )
        builder.generative_step(
            operator=Operator.GENERATION,  # Hard
            inputs=[Read.new(key="first_prompt", required=True)],
            prompt="{{first_prompt}}",
            outputs=[Write.new("response")],  # Hard
        )
        builder.generative_step(
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="second_prompt", required=True),
                Read.new(key="response", required=True),
            ],
            prompt="{{second_prompt}} {{response}}",
            outputs=[Write.new("result")],
        )
        flow = [Edge(source="0", target="1"), Edge(source="1", target="_end")]  # End
        builder.flow(flow)

        builder.set_return_value("result")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        return [self.OutputSchema(**{"output": r.result}) for r in result]


async def main():
    return await dria.generate(
        {
            "first_prompt": "Generate tweet about football",
            "second_prompt": "Extend the tweet",
        },
        workflow=SimpleWorkflow,
        models=Model.GPT4O,
    )


if __name__ == "__main__":
    print(asyncio.run(main()))
