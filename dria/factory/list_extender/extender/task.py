import logging
from dria.models import TaskInput
from dria.factory.utilities import get_abs_path, parse_json, get_tags
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Workflow,
)
from typing import Dict, List
from dria.pipelines import Step, StepTemplate


logger = logging.getLogger(__name__)


class ListExtender(StepTemplate):

    def create_workflow(self, e_list: List[str]) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param e_list: The description of the simulation.
        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(e_list=e_list)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)
        # Step A: RandomVarGen
        builder.generative_step(
            id="extend_list",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("extended_list")],
        )

        flow = [
            Edge(source="extend_list", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("extended_list")
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
        new_list = parse_json(
            get_tags(output, "extended_list")[0].replace("\n", "").replace("'", '"')
        )
        return [TaskInput(**{"topic": el}) for el in new_list + step.input[0].e_list]
