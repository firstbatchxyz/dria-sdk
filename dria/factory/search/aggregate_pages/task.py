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
        builder.set_max_time(50)
        builder.set_max_tokens(750)

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
    def parse(result: str) -> Any:
        lines = result.strip().split("\n")

        # Initialize list for storing parsed articles
        articles = []

        # Process each article (5 lines per article)
        for i in range(0, len(lines), 5):
            title = lines[i].strip()
            url = lines[i + 1].strip()
            summary = lines[i + 2].strip()
            date = lines[i + 3].strip()
            article_id = int(lines[i + 4].strip())

            articles.append(
                TaskInput(
                    **{
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "date": date,
                        "id": article_id,
                    }
                )
            )
        return articles
