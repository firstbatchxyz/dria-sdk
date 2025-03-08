
from dria import Dria, WorkflowTemplate, Model


class SimpleWorkflow(WorkflowTemplate):

    def define_workflow(self) -> None:
        self.add_step("Write a short story about a {{topic}}")


async def main():
    """
    Main function to demonstrate the execution of a custom workflow.
    
    Initializes the Dria client, configures a workflow with inputs,
    and executes it with the specified model.
    """
    dria = Dria()
    return await dria.generate(
        inputs={
            "topic": "robot learning to paint"
        },
        workflow=SimpleWorkflow,
        models=Model.GEMINI
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
