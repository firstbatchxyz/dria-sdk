from typing import List, Dict, Union, Any
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Read,
    Write,
    Edge,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
from dria.factory.persona.utils import sample_variable
import json_repair


class RandomVarOutput(BaseModel):
    persona_traits: List[str] = Field(..., description="List of persona traits")
    simulation_description: str = Field(
        ..., description="Description of the simulation"
    )
    model: str = Field(..., description="Model used for generation")


class RandomVariables(BaseModel):
    variables: List[RandomVarOutput] = Field(..., description="List of variables")
    model: str = Field(..., description="Model name")


class RandomVars(SingletonTemplate):
    # Input fields
    simulation_description: str = Field(
        ..., description="Description of the simulation"
    )
    num_of_samples: int = Field(default=1, description="Number of samples to generate")

    # Output schema
    OutputSchema = RandomVarOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating random variables.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(simulation_description=self.simulation_description)
        builder.set_max_time(65)
        builder.set_max_tokens(800)
        # Step A: RandomVarGen
        builder.generative_step(
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="simulation_description", required=True),
                Read.new(key="is_valid", required=False),
            ],
            outputs=[Write.new("random_vars")],
        )

        flow = [
            Edge(source="0", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("random_vars")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[RandomVarOutput]:
        """
        Parse the results into validated RandomVarOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[RandomVarOutput]: List of validated random variable outputs
        """
        outputs: List[RandomVarOutput] = []
        for r in result:
            variables = []
            try:
                parsed_vars = self.parse_json(r.result)
                for _ in range(self.num_of_samples):
                    persona_traits = [
                        f"{var['description']}: {sample_variable(var)}".replace("'", "")
                        for var in parsed_vars
                    ]
                    variables.append(
                        RandomVarOutput(
                            persona_traits=persona_traits,
                            simulation_description=self.simulation_description,
                            model=r.model,
                        )
                    )
                outputs.extend(variables)
            except Exception as e:
                raise e
        return outputs

    @staticmethod
    def parse_json(text: Union[str, List]) -> Union[List[Dict], Dict]:
        """
        Parse the JSON text.

        Args:
            text: The text to parse.

        Returns:
            Parsed JSON output.
        """

        def parse_single_json(t: str) -> Any:
            return json_repair.loads(t)

        if isinstance(text, list):
            return [parse_single_json(item) for item in text]
        else:
            return parse_single_json(text)
