import asyncio
from typing import List

from pydantic import BaseModel, Field

from dria import Model, Dria, WorkflowTemplate
from dria.models import TaskResult

dria = Dria()

class SimpleWorkflow(WorkflowTemplate):

    def define_workflow(self):
        step1 = self.add_step(
            prompt="{{first_step}}",
            output="response"
        )
        step2 = self.add_step(
            prompt="{{second_step}} {{response}}",
        )
        self.connect(step1, step2)


async def main():
    return await dria.generate(
        {
            "first_step": "Generate tweet about football",
            "second_step": "Extend the tweet",
        },
        workflow=SimpleWorkflow,
        models=Model.GEMINI,
    )


if __name__ == "__main__":
    print(asyncio.run(main()))
