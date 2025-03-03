import logging
from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Operator,
)
from dria.workflow.factory.utilities import parse_json
from dria.workflow.template import WorkflowTemplate
from dria.models import TaskResult


class WebSearchResult(BaseModel):
    query: str = Field(..., description="Query used for search")
    link: str = Field(..., description="Link of the search result")
    snippet: str = Field(..., description="Snippet of the search result")
    title: str = Field(..., description="Title of the search result")


class SearchWeb(WorkflowTemplate):
    OutputSchema = WebSearchResult

    def define_workflow(self):
        """
        Creates a workflow for generating subtopics for a given topic.
        """

        # Initialize the workflow with variables
        self.add_step(
            operation=Operator.SEARCH,
            prompt="{{query}}",
            search_lang="en",
            search_n_results=5,
            outputs=["results"],
        )
        self.set_output("results")

    def callback(self, result: List[TaskResult]) -> List[OutputSchema]:
        """
        Parse the results into validated SubtopicsOutput objects

        Args:
            result: List of TaskResult objects

        Returns:
            List[OutputSchema]: List of validated subtopics outputs
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
                data["query"] = r.task_input["query"]
                results.append(self.OutputSchema(**data))
        return results
