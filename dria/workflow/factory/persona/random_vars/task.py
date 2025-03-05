from typing import List, Dict, Union, Any
from pydantic import BaseModel, Field
from dria.workflow.factory.utilities import get_abs_path
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult
from dria.workflow.factory.persona.utils import sample_variable
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


class RandomVars(WorkflowTemplate):

    # Output schema
    OutputSchema = RandomVarOutput

    def define_workflow(self):
        """
        Creates a workflow for generating random variables.
        """
        self.add_step(
            prompt=get_abs_path("prompt.md"),
            outputs=["random_vars"],
        )

        self.set_output("random_vars")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated OutputSchema objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated random variable outputs
        """
        outputs: List[RandomVarOutput] = []
        for r in result:
            variables = []
            try:
                parsed_vars = self.parse_json(r.result)
                for _ in range(int(r.inputs["num_of_samples"])):
                    persona_traits = [
                        f"{var['description']}: {sample_variable(var)}".replace("'", "")
                        for var in parsed_vars
                    ]
                    variables.append(
                        self.OutputSchema(
                            persona_traits=persona_traits,
                            simulation_description=r.inputs["simulation_description"],
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
