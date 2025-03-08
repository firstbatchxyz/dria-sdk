from dria import Dria, WorkflowTemplate, Model


class SimpleWorkflow(WorkflowTemplate):
    """
    A two-step workflow that generates content and then refines it.
    
    This workflow demonstrates how to create a multi-hop process where:
    1. The first step generates initial content based on a prompt
    2. The second step takes that content and transforms it based on another prompt
    3. The steps are explicitly connected to form a processing pipeline
    """

    def define_workflow(self) -> None:
        """
        Define the workflow structure with multiple steps and connections.
        
        This method sets up two processing steps and connects them to create
        a data flow where the output of the first step becomes input to the second.
        """
        step1 = self.add_step("{{first_prompt}}", output="response")
        step2 = self.add_step(
            "{{second_prompt}} {{response}}", inputs=["response"])
        self.connect(step1, step2)


async def main():
    """
    Main function to demonstrate the execution of a multi-hop workflow.
    
    Initializes the Dria client, configures a workflow with inputs for both steps,
    and executes it with the specified model.
    """
    dria = Dria()
    return await dria.generate(
        inputs={
            "first_prompt": "write tweet about AI",
            "second_prompt": "extend tweet to article"
        },
        workflow=SimpleWorkflow,
        models=Model.GEMINI
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(main()))
