import json
import random
from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    GetAll,
    Push,
    Edge,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult, TaskInput


class SearchResult(BaseModel):
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    summary: str = Field(..., description="Summary or snippet of the search result")
    id: str = Field(..., description="Unique identifier for the result")


class SearchOutput(BaseModel):
    results: List[SearchResult] = Field(..., description="List of search results")
    model: str = Field(..., description="Model used for generation")


class PageAggregator(SingletonTemplate):
    # Input fields
    topic: str = Field(..., description="Topic to search for")

    # Output schema
    OutputSchema = SearchOutput

    def workflow(self) -> Workflow:
        """
        Creates a workflow for searching and aggregating pages related to a topic.

        Returns:
            Workflow: The constructed workflow
        """
        builder = WorkflowBuilder(topic=self.topic)

        builder.generative_step(
            path=get_abs_path("search.md"),  # You'll need to create this template
            operator=Operator.FUNCTION_CALLING,
            inputs=[GetAll.new("topic", required=True)],
            outputs=[Push.new("links")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("links")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[SearchOutput]:
        """
        Parse the results into validated SearchOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SearchOutput]: List of validated search outputs
        """
        return [
            SearchOutput(
                results=self.parse_results(json.loads(r.result)), model=r.model
            )
            for r in result
        ]

    @staticmethod
    def parse_results(data: str) -> List[SearchResult]:
        """
        Parse the search results into SearchResult objects

        Args:
            data: Raw search result data

        Returns:
            List[SearchResult]: List of parsed and validated search results
        """
        try:
            # Try parsing as JSON
            if isinstance(data, list):
                return [
                    SearchResult(
                        title=item["title"],
                        url=f"https://{item['link']}",
                        summary=item["snippet"],
                        id=str(random.randint(10000, 99999)),
                    )
                    for item in data
                ]
            else:
                # Parse newline-separated format
                lines = data.strip().split("\n")
                return [
                    SearchResult(
                        title=lines[i].strip(),
                        url=lines[i + 1].strip(),
                        summary=lines[i + 2].strip(),
                        id=lines[i + 4].strip(),
                    )
                    for i in range(0, len(lines), 5)
                ]
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise ValueError(f"Error parsing search results: {str(e)}")
