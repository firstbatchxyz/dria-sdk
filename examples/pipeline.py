"""
Multi-Stage Workflow Pipeline Example

This example demonstrates how to create and execute a multi-stage workflow pipeline
using the Dria SDK. It shows how to:

1. Define multiple workflow templates that can be chained together
2. Configure a dataset to store intermediate and final results
3. Execute the workflow pipeline with specified models
4. Transform data between pipeline stages using callbacks

The example creates a two-stage pipeline where:
- The first workflow generates initial content based on a prompt
- The second workflow takes that content and expands it into a full article
- Results flow automatically between the workflows through the dataset

This pattern can be extended to create complex multi-stage AI pipelines with
data transformations between stages.

Usage:
    python examples/pipeline.py

Requirements:
    - Dria SDK installed
    - Valid Dria API credentials configured
"""

from typing import List, Any

from dria import Dria, WorkflowTemplate, Model, DriaDataset, TaskResult


class FirstWorkflow(WorkflowTemplate):
    """
    First workflow in the pipeline.
    
    This workflow takes a prompt as input and generates initial content.
    The callback transforms the raw results into a structured format
    that can be consumed by the next workflow in the pipeline.
    """
    def define_workflow(self) -> None:
        self.add_step("{{prompt}}", outputs=["result"])
        self.set_output("result")

    def callback(self, result: List[TaskResult]) -> Any:
        return [{"idea": r.result for r in result}]


class SecondWorkflow(WorkflowTemplate):
    """
    Second workflow in the pipeline.
    
    This workflow takes the structured output from the first workflow
    and expands it into a full article. It demonstrates how to use
    the output of a previous workflow as input to a subsequent one.
    """
    def define_workflow(self) -> None:
        self.add_step("Expand on this to article: {{idea}}", inputs=["idea"], outputs=["expanded"])
        self.set_output("expanded")


async def main():
    """
    Main function to demonstrate the execution of a multi-stage workflow pipeline.
    
    Initializes the Dria client, configures a dataset for storing results,
    and executes a two-stage workflow pipeline with the specified model.
    """
    dria = Dria()

    dataset = DriaDataset(collection="pipeline_test")  # Dataset is required for pipelines
    # Execute workflows in a pipeline
    return await dria.generate(
        inputs={
            "prompt": "Write a short story about a robot learning to paint"
        },
        workflow=[FirstWorkflow, SecondWorkflow],
        models=Model.GEMINI,
        dataset=dataset
    )


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(main()))
