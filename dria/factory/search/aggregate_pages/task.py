import json
import logging
import random
from typing import Dict, List

from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    Workflow,
)

from dria.models import TaskInput
from dria.pipelines import Step, StepTemplate

logger = logging.getLogger(__name__)


class PageAggregator(StepTemplate):

    def create_workflow(
        self,
        topic: str,
    ) -> Workflow:
        """Collect web pages related to topic

        Args:
            :param topic:

        Returns:
            dict: collected pages
        """
        builder = WorkflowBuilder(topic=topic)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: RandomVarGen
        builder.generative_step(
            id="search",
            prompt="Search for following topic: {{topic}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[
                Read.new(key="topic", required=True),
            ],
            outputs=[Write.new("links")],
        )

        flow = [Edge(source="search", target="_end")]
        builder.flow(flow)
        builder.set_return_value("links")
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

        return self.parse(step.output[0].result)

    @staticmethod
    def parse(result: str) -> List[TaskInput]:
        """
        Parse input string into a list of TaskInput objects.

        Args:
            result (str): Input string in either JSON format or newline-separated format

        Returns:
            List[TaskInput]: List of parsed TaskInput objects
        """
        try:
            # Try parsing as JSON first
            data = json.loads(result)
            return [
                TaskInput(
                    title=item["title"],
                    url=f"https://{item['link']}",
                    summary=item["snippet"],
                    id=str(random.randint(10000, 99999)),
                )
                for item in data
            ]
        except json.JSONDecodeError:
            # Fall back to parsing newline-separated format
            lines = result.strip().split("\n")
            return [
                TaskInput(
                    title=lines[i].strip(),
                    url=lines[i + 1].strip(),
                    summary=lines[i + 2].strip(),
                    id=int(lines[i + 4].strip()),
                )
                for i in range(0, len(lines), 5)
            ]
