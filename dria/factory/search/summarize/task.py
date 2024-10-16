import logging
from dria.models import TaskInput
from dria_workflows import WorkflowBuilder, Operator, Push, Read, Edge, Peek, Workflow
from typing import Dict, List, Any, TypedDict
from dria.pipelines import Step, StepTemplate
import json

logger = logging.getLogger(__name__)


class Article(TypedDict):
    title: str
    url: str
    summary: str
    date: str
    id: int


class PageSummarizer(StepTemplate):

    def create_workflow(
        self,
        article: Article,
    ) -> Workflow:
        """Collect web pages related to topic

        Args:
            :param article:

        Returns:
            dict: collected pages
        """
        builder = WorkflowBuilder(url=article["url"])
        builder.set_max_time(50)
        builder.set_max_steps(5)
        builder.set_max_tokens(750)

        builder.generative_step(
            id="search",
            prompt="Scrape following url: {{url}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[
                Read.new(key="url", required=True),
            ],
            outputs=[Push.new("content")],
        )
        if self.params.summarize:
            builder.generative_step(
                id="summarize",
                prompt="Read the following content: {{content}}\n\n Summarize it in 1 or 2 paragraphs. "
                "Output summary and nothing else.Summary:",
                operator=Operator.GENERATION,
                inputs=[
                    Peek.new(key="content", index=0, required=True),
                ],
                outputs=[Push.new("content")],
            )

            flow = [
                Edge(source="search", target="summarize", fallback="0"),
                Edge(source="summarize", target="_end"),
            ]
        else:
            flow = [
                Edge(source="search", target="_end", fallback="0"),
            ]
        builder.flow(flow)
        builder.set_return_value("content")
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
        results = []
        for i, o in enumerate(step.output):
            res = self.parse(o.result)
            res.update({"url": step.input[i].url})
            res.update({"summary": step.input[i].summary})
            results.append(TaskInput(**res))
        return results

    def parse(self, result) -> Dict[str, str]:
        parsed = json.loads(result)
        if len(parsed) == 2:
            return {"content": parsed[0], "llm_summary": parsed[1]}
        elif len(parsed) == 1:
            return {"content": parsed[0]}
        else:
            raise ValueError("Unexpected number of outputs from summarizer")
