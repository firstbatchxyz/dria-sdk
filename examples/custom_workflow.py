"""
Custom Workflow Example

This example demonstrates how to create a simple custom workflow using the Dria SDK.
It shows how to define a basic workflow template, configure inputs, and execute
the workflow with a specified model.

The SimpleWorkflow class defines a single-step workflow that processes a prompt
and returns the result. This pattern can be extended to create more complex
multi-step workflows with custom logic.

Usage:
    python examples/custom_workflow.py

Requirements:
    - Dria SDK installed
    - Valid Dria API credentials configured
"""

from dria import Dria, WorkflowTemplate, Model


class SimpleWorkflow(WorkflowTemplate):
    """
    A simple workflow that processes a single prompt and returns the result.
    
    This workflow demonstrates the basic structure of a Dria workflow template,
    with a single step that takes a prompt as input and produces a result.
    """

    def define_workflow(self) -> None:
        """
        Define the workflow structure with steps and connections.
        
        This method is required for all workflow templates and sets up the
        processing steps and data flow of the workflow.
        """
        self.add_step("{{prompt}}", outputs=["result"])
        self.set_output("result")


async def main():
    """
    Main function to demonstrate the execution of a custom workflow.
    
    Initializes the Dria client, configures a workflow with inputs,
    and executes it with the specified model.
    """
    dria = Dria()
    return await dria.generate(
        inputs={
            "prompt": "Write a short story about a robot learning to paint"
        },
        workflow=SimpleWorkflow,
        models=Model.GEMINI
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(main()))
