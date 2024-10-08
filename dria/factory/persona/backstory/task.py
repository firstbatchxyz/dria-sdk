from dria.models import TaskInput
from dria.factory.utilities import get_abs_path
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    GetAll,
    Workflow,
)
import json

import logging
from typing import List
from dria.pipelines import Step, StepTemplate


logger = logging.getLogger(__name__)


class BackStory(StepTemplate):
    def create_workflow(
        self, persona_traits: List[str], simulation_description: str, **kwargs
    ) -> Workflow:
        """Generate a backstory for a simulation persona.

        Args:
            :param persona_traits: The traits of the persona.
            :param simulation_description: The description of the simulation.
            :param max_time: The maximum time to run the workflow. Defaults to 300.
            :param max_steps: The maximum number of steps to run the workflow. Defaults to 20.
            :param max_tokens: The maximum number of tokens to run the workflow. Defaults to 750.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(
            persona_traits=persona_traits, simulation_description=simulation_description
        )

        # Step A: GenerateBackstory
        builder.generative_step(
            id="generate_backstory",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="simulation_description", required=True),
                GetAll.new(key="persona_traits", required=True),
            ],
            outputs=[Write.new("backstory")],
        )

        flow = [Edge(source="generate_backstory", target="_end")]
        builder.flow(flow)
        builder.set_return_value("backstory")
        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the backstory generation step.

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            List[TaskInput]: A list of TaskInput objects for the next step.

        Raises:
            Exception: If there's an error processing the step output.
        """

        try:
            return [
                TaskInput(backstory=self.parse(backstory.result))
                for backstory in step.output
            ]
        except Exception as e:
            logger.error(f"Error in backstory_callback: {str(e)}")
            raise

    @staticmethod
    def parse(result: str) -> List[str]:
        """Parse the backstory JSON.

        Args:
            result (str): The JSON string containing the backstory.

        Returns:
            List[str]: The parsed backstory as a list of strings.
        """
        try:
            parsed = json.loads(result.replace("```json", ""))
            backstory = parsed.get("backstory", [])
            return backstory if isinstance(backstory, list) else [backstory]
        except json.JSONDecodeError:
            return [result]


if __name__ == "__main__":
    d = BackStory(
        persona_traits=["", ""], simulation_description="simulation_description"
    )

    print("")
