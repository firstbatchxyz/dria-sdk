"""
Multi-hop Custom Workflow Example

This example demonstrates how to create a multi-step workflow using the Dria SDK.
It shows how to define a workflow template with multiple connected steps, configure
inputs for each step, and execute the workflow with a specified model.

The SimpleWorkflow class defines a two-step workflow that:
1. Generates a tweet about AI using the first prompt
2. Takes that tweet and extends it into an article using the second prompt

This pattern can be extended to create more complex multi-step workflows with
custom logic and data flow between steps.

Usage:
    python examples/multihop_custom_workflow.py

Requirements:
    - Dria SDK installed
    - Valid Dria API credentials configured
"""

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
        step1 = self.add_step("{{first_prompt}}", outputs=["response"])
        step2 = self.add_step(
            "{{second_prompt}} {{response}}", inputs=["response"], outputs=["result"]
        )
        self.connect(step1, step2)
        self.set_output("result")


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
