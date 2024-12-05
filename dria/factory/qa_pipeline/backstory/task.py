from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    GetAll,
    Read,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class BackstoryOutput(BaseModel):
    backstory: str = Field(..., description="Generated backstory")
    model: str = Field(..., description="Model used for generation")


class BackStory(SingletonTemplate):
    # Input fields
    persona_traits: List[str] = Field(..., description="The traits of the persona")
    simulation_description: str = Field(..., description="The description of the simulation")
    max_time: int = Field(default=75, description="Maximum time to run the workflow")
    max_steps: int = Field(default=20, description="Maximum number of steps")
    max_tokens: int = Field(default=750, description="Maximum number of tokens")

    # Output schema
    OutputSchema = BackstoryOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating backstory.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(
            persona_traits=self.persona_traits,
            simulation_description=self.simulation_description
        )

        # Set workflow constraints
        builder.set_max_time(self.max_time)
        builder.set_max_steps(self.max_steps)
        builder.set_max_tokens(self.max_tokens)

        # Generate backstory step
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

        # Define workflow flow
        flow = [Edge(source="generate_backstory", target="_end")]
        builder.flow(flow)

        # Set return value
        builder.set_return_value("backstory")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[BackstoryOutput]:
        """
        Parse the results into validated BackstoryOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[BackstoryOutput]: List of validated backstory outputs
        """
        if not result:
            raise ValueError("Backstory generation failed")

        return [
            BackstoryOutput(
                backstory=r.result,
                model=r.model
            )
            for r in result
        ]