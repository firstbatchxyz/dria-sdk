import logging
from dria.models import TaskInput
from dria.factory.utilities import get_abs_path
from dria.utils.task_utils import parse_json
from typing import Any
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    Workflow,
    ConditionBuilder,
    Expression,
)
import random
from typing import Dict, List
from dria.pipelines import Step, StepTemplate


logger = logging.getLogger(__name__)


class RandomVariable(StepTemplate):

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
        builder.set_max_time(90)
        builder.set_max_tokens(750)

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
            output = parse_json(output)
            inputs = []
            for _ in range(self.params.num_samples):
                persona_traits = [
                    f"{var['description']}: {self.sample_variable(var)}".replace(
                        "'", ""
                    )
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
            logger.error(f"Error in random_var_callback: {str(e)}")
            raise

    @staticmethod
    def sample_variable(variable: Dict[str, Any]) -> Any:
        """Sample a variable from the given dictionary.

        Args:
            variable (Dict[str, Any]): The variable to sample from.

        Raises:
            ValueError: If the variable type is not supported.

        Returns:
            Any: The sampled variable.
        """
        var_type = variable["type"]
        if var_type == "categorical":
            return random.choice(variable["values"])
        elif var_type == "numerical":
            return int(
                random.uniform(variable["values"]["min"], variable["values"]["max"])
            )
        elif var_type == "binary":
            return random.choice(["True", "False"])
        raise ValueError(f"Unsupported variable type: {var_type}")
