import logging
from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Write,
    Edge,
)
from dria.factory.utilities import parse_json
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult


class WebSearchResult(BaseModel):
    query: str = Field(..., description="Query used for search")
    link: str = Field(..., description="Link of the search result")
    snippet: str = Field(..., description="Snippet of the search result")
    title: str = Field(..., description="Title of the search result")


class SearchWeb(SingletonTemplate):
    # Input fields
    query: str = Field(..., description="Query to search for")
    lang: str = Field("en", description="Language to search in")
    n_results: int = Field(5, gt=0, lte=25, description="Number of results to return")

    # Output schema
    OutputSchema = WebSearchResult

    def workflow(self) -> Workflow:
        """
        Creates a workflow for generating subtopics for a given topic.

        Returns:
            Workflow: The constructed workflow
        """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(query=self.query)

        # Generate subtopics
        builder.search_step(
            search_query="{{query}}",
            lang=self.lang,
            n_results=self.n_results,
            outputs=[Write.new("results")],
        )

        # Define the flow
        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("results")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[WebSearchResult]:
        """
        Parse the results into validated SubtopicsOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[SubtopicsOutput]: List of validated subtopics outputs
        """
        results = []
        for r in result:
            try:
                parsed_ = parse_json(r.result)["organic"]
            except Exception as e:
                logging.debug(e)
                parsed_ = parse_json(r.result)

            for d in parsed_:
                data = {key: d[key] for key in ["link", "snippet", "title"] if key in d}
                data["query"] = self.query
                results.append(WebSearchResult(**data))
        return results
