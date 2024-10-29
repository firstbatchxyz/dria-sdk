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


class ExtendCSV(StepTemplate):

    def create_workflow(
        self,
        csv: str,
        seed_column: str,
    ) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param csv: The description of the simulation.
            :param seed_column: The column to extend.

        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(csv=csv, seed_column=seed_column)
        builder.set_max_time(90)
        builder.set_max_tokens(1000)

        # Step A: RandomVarGen
        builder.generative_step(
            id="extend_csv",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            outputs=[Write.new("extended")],
        )

        flow = [
            Edge(source="extend_csv", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("extended")
        return builder.build()

    def callback(self, step: Step) -> TaskInput:
        """
        Process the output of the random variable generation step.

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            Dict[str, Any]: A dictionary containing persona traits and simulation description.

        Raises:
            Exception: If there's an error processing the step output.
        """
        extended = step.input[0].csv + "\n"
        for r in step.output:
            extended += r.result.replace("```csv", "").replace("```", "").strip() + "\n"
        return TaskInput(**{"extended_csv": extended})
