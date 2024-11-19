import json
import logging
from dria.models import TaskInput
from dria.factory.utilities import get_abs_path
from dria.utils.task_utils import parse_json
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
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Dependency(BaseModel):
    column: str = Field(..., title="The dependent column")
    dependencies: List[str] = Field(..., title="The independent columns")
    independent: bool = Field(..., title="Whether the column is independent")


class Dependecies(BaseModel):
    dependencies: List[Dependency] = Field(..., title="The dependencies")


class GetDependencies(StepTemplate):

    def create_workflow(
        self,
        csv: str,
    ) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param csv: The description of the simulation.

        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(csv=csv)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: RandomVarGen
        builder.generative_step(
            id="get_dependencies",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
            schema=Dependecies,
            inputs=[
                Read.new(key="csv", required=True),
            ],
            outputs=[Write.new("dependencies")],
        )

        flow = [
            Edge(source="get_dependencies", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("dependencies")
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
        independent_dependencies = [
            col["column"]
            for col in parse_json(output)["dependencies"]
            if col["independent"]
        ]
        return [
            TaskInput(
                **{
                    "independent_columns": val,
                    "csv": step.input[0].csv,
                    "num_values": self.params.num_values,
                }
            )
            for val in independent_dependencies
        ]


class PopulatedExamples(BaseModel):
    example: List[str] = Field(..., title="The list of new examples")


class PopulateDependencies(StepTemplate):

    def create_workflow(
        self, independent_columns: str, csv: str, num_values: str
    ) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param independent_columns: The description of the simulation.
            :param csv: The description of the simulation.
        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(
            csv=csv, independent_columns=independent_columns, num_values=num_values
        )
        builder.set_max_time(90)
        builder.set_max_tokens(1000)

        # Step A: RandomVarGen
        builder.generative_step(
            id="get_dependencies",
            path=get_abs_path("populate.md"),
            schema=PopulatedExamples,
            operator=Operator.GENERATION,
            outputs=[Write.new("dependencies")],
        )

        flow = [
            Edge(source="get_dependencies", target="_end"),
        ]
        builder.flow(flow)
        builder.set_return_value("dependencies")
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
        examples = parse_json(output)["example"]
        return [
            TaskInput(
                **{
                    "csv": step.input[0].csv,
                    "seed_column": ex,
                    "num_rows": self.params.num_rows,
                }
            )
            for ex in examples
        ]
