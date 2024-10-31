from typing import List, Union, Dict

import json_repair

from dria.factory.qa_pipeline.utils import sample_variable
from dria.models import TaskInput
from dria.pipelines import StepTemplate, Step
from dria_workflows import (
    WorkflowBuilder,
    ConditionBuilder,
    Operator,
    Write,
    Edge,
    Read,
    Expression,
    Workflow,
)
from dria.factory.utilities import get_abs_path


class RandomVarsStep(StepTemplate):

    def create_workflow(
        self,
        simulation_description: str,
    ) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param simulation_description: The description of the simulation.

        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(simulation_description=simulation_description)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)

        # Step A: RandomVarGen
        builder.generative_step(
            id="random_var_gen",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="simulation_description", required=True),
                Read.new(key="is_valid", required=False),
            ],
            outputs=[Write.new("random_vars")],
        )

        # Step B: ValidateRandomVars
        builder.generative_step(
            id="validate_random_vars",
            path=get_abs_path("validate.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new(key="simulation_description", required=True),
                Read.new(key="random_vars", required=True),
            ],
            outputs=[Write.new("is_valid")],
        )

        flow = [
            Edge(source="random_var_gen", target="validate_random_vars"),
            Edge(
                source="validate_random_vars",
                target="_end",
                condition=ConditionBuilder.build(
                    input=Read.new("random_vars", required=True),
                    expression=Expression.EQUAL,
                    expected="Yes",
                    target_if_not="A",
                ),
            ),
        ]
        builder.flow(flow)
        builder.set_return_value("random_vars")
        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the random variable generation step.

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            Dict[str, Any]: A dictionary containing persona traits and simulation description.

        Raises:
            Exception: If there's an error processing the step output.
        """

        output = step.output[0].result
        try:
            output = self.parse_json(output)
            inputs = []
            for _ in range(self.params.num_of_samples):
                persona_traits = [
                    f"{var['description']}: {sample_variable(var)}".replace("'", "")
                    for var in output
                ]
                inputs.append(
                    TaskInput(
                        persona_traits=persona_traits,
                        simulation_description=step.all_inputs[
                            0
                        ].simulation_description,
                    )
                )
            return inputs
        except Exception as e:
            raise e

    @staticmethod
    def parse_json(text: Union[str, List]) -> Union[list[dict], dict]:
        """Parse the JSON text.

        Args:
            text (str): The text to parse.

        Returns:
            dict: JSON output.
        """

        def parse_single_json(t: str) -> Dict:
            return json_repair.loads(t)

        if isinstance(text, list):
            return [parse_single_json(item) for item in text]
        else:
            return parse_single_json(text)
