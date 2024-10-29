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
        builder.set_max_time(90)
        builder.set_max_tokens(1000)

        # Step A: RandomVarGen
        builder.generative_step(
            id="get_dependencies",
            path=get_abs_path("prompt.md"),
            operator=Operator.GENERATION,
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
        independent_dependencies = []
        for dep in output.split("\n"):
            if dep:
                if "-> independent" in dep:
                    dep = dep.replace("-> independent", "").strip()
                    independent_dependencies.append(dep)

        return [
            TaskInput(**{"independent_columns": val, "csv": step.input[0].csv})
            for val in independent_dependencies
        ]


class PopulateDependencies(StepTemplate):

    def create_workflow(self, independent_columns: str, csv: str) -> Workflow:
        """Generate random variables for simulation

        Args:
            :param independent_columns: The description of the simulation.
            :param csv: The description of the simulation.
        Returns:
            dict: The generated random variables.
        """
        builder = WorkflowBuilder(csv=csv, independent_columns=independent_columns)
        builder.set_max_time(90)
        builder.set_max_tokens(1000)

        # Step A: RandomVarGen
        builder.generative_step(
            id="get_dependencies",
            path=get_abs_path("populate.md"),
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
        data = parse_json(output)
        column_name = step.input[0].independent_columns
        examples = data[column_name]
        # populate multiple csvs, with a column filled and rest empty. Fill the rest to AI

        return [
            TaskInput(**{"csv": step.input[0].csv, "seed_column": ex})
            for ex in examples
        ]

    @staticmethod
    def get_columns(csv: str, column: str) -> List[str]:
        lines = csv.split("\n")
        column_index = lines[0].split(",").index(column)
        for i in range(1, len(lines)):
            yield lines[i].split(",")[column_index]

    @staticmethod
    def add_colums(csv: str, column: str, columns: List[str]) -> str:
        lines = csv.split("\n")
        num_columns = len(columns)
        column_index = lines[0].split(",").index(column)
        for i in range(1, len(lines)):
            line = ""
            for j in range(num_columns):
                if j == column_index:
                    line += columns[j] + ","
                else:
                    line += ","
            line += "\n"
            lines[i] = line
        return "\n".join(lines)
