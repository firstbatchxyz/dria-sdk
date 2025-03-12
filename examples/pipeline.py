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
        self.add_step("{{prompt}}")

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
        self.add_step("Expand on this to article: {{idea}}")


async def main():
    """
    Main function to demonstrate the execution of a multi-stage workflow pipeline.

    Initializes the Dria client, configures a dataset for storing results,
    and executes a two-stage workflow pipeline with the specified model.
    """
    dria = Dria()

    dataset = DriaDataset(
        collection="pipeline_test"
    )  # Dataset is required for pipelines
    # Execute workflows in a pipeline
    return await dria.generate(
        inputs={"prompt": "Write a short story about a robot learning to paint"},
        workflow=[FirstWorkflow, SecondWorkflow],
        models=Model.GEMINI,
        dataset=dataset,
    )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(main()))
