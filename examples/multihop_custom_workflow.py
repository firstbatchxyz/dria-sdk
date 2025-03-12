from typing import List

from dria import Dria, WorkflowTemplate, Model, TaskResult


class SubtopicGeneratorWorkflow(WorkflowTemplate):
    def define_workflow(self) -> None:
        # Generate main topic
        step1 = self.add_step(
            "Generate a main topic about {{domain}}", output="main_topic"
        )

        # Generate subtopics based on the main topic
        step2 = self.add_step(
            "List smaller subtopics related to {{main_topic}}",
            inputs=["main_topic"],
            output="subtopics",
        )

        # Generate content for each subtopic
        step3 = self.add_step(
            "Write a short paragraph about {{subtopics}}",
            inputs=[self.get_list("subtopics")],
            output="content",
        )

        self.connect(step1, step2)
        self.connect(step2, step3)

    def callback(self, result: List[TaskResult]):
        return result


async def main():
    """
    Main function to demonstrate the execution of a multi-hop workflow.

    Initializes the Dria client, configures a workflow with inputs for both steps,
    and executes it with the specified model.
    """
    dria = Dria()
    return await dria.generate(
        inputs={
            "domain": "AI",
        },
        workflow=SubtopicGeneratorWorkflow,
        models=Model.GEMINI,
    )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(main()))
