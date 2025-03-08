import asyncio
from typing import List

from pydantic import BaseModel, Field

from dria import Model, Dria, WorkflowTemplate
from dria.models import TaskResult

dria = Dria()


class SimpleClass(BaseModel):
    output: str = Field(...)


class SimpleWorkflow(WorkflowTemplate):
    OutputSchema = SimpleClass

    def define_workflow(self):
        self.add_step(
            prompt="{{first_step}}",
            output="response"
        )
        self.add_step(
            prompt="{{second_prompt}} {{response}}",
        )

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
