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
from dria.factory.utilities import get_abs_path, parse_json
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from dria.utils import logger


class BackstoryOutput(BaseModel):
    backstory: str = Field(..., description="Generated backstory")
    model: str = Field(..., description="Model used for generation")


class BackStory(SingletonTemplate):
    # Input fields
    persona_traits: List[str] = Field(..., description="The traits of the persona")
    simulation_description: str = Field(
        ..., description="The description of the simulation"
    )

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
            simulation_description=self.simulation_description,
        )

        # Set workflow constraints
        builder.set_max_time(65)
        builder.set_max_steps(3)
        builder.set_max_tokens(750)

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

        outputs = []
        for r in result:
            try:
                backstory = parse_json(r.result)["backstory"]
            except Exception as e:
                logger.debug(e)
                backstory = r.result

            outputs.append(BackstoryOutput(backstory=backstory, model=r.model))

        return outputs
