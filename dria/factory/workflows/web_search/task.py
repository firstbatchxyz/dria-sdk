from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Push,
    Edge,
    Read,
    GetAll,
    Write,
    Pop,
    ConditionBuilder,
    Expression,
    Size,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate
from typing import Literal
import re

Mode = Literal[
    "WIDE",
    "NARROW",
]


class WebSearch(SingletonTemplate):
    """
    A workflow to answer multiple-choice questions using web search and evaluation.
    """

    def workflow(self, topic: str, mode: Mode) -> Workflow:
        """ """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(topic=topic)
        builder.set_max_time(200)
        builder.set_max_tokens(750)

        if mode == "WIDE":
            self.params.num_turns = 3
        elif mode == "NARROW":
            self.params.num_turns = 1
        else:
            raise ValueError(f"Invalid mode: {mode}")

        # Add a generative step using the prompt
        builder.generative_step(
            prompt="Learn more about {{topic}}. Use previous queries to avoid duplication: {{history}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[
                Read.new("topic", required=True),
                GetAll.new("history", required=False),
            ],
            outputs=[Write.new("search"), Push.new("history")],
        )

        builder.generative_step(
            path=get_abs_path("pick_url.md"),
            operator=Operator.GENERATION,
            inputs=[Read.new("search", required=True)],
            outputs=[Write.new("url")],
        )

        builder.generative_step(
            prompt="Scrape {{url}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[Read.new("url", required=True)],
            outputs=[Write.new("search_results")],
        )

        builder.generative_step(
            path=get_abs_path("notes.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new("search_results", required=True),
            ],
            outputs=[Push.new("notes")],
        )

        flow = [
            Edge(source="0", target="1"),
            Edge(source="1", target="2"),
            Edge(source="2", target="3", fallback="0"),
            Edge(
                source="3",
                target="_end",
                fallback="0",
                condition=ConditionBuilder.build(
                    self.params.num_turns,
                    Expression.GREATER_THAN_OR_EQUAL,
                    Size.new("notes", required=True),
                    target_if_not="0",
                ),
            ),
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("notes")
        return builder.build()

    def parse_result(self, result):
        # take between tags <summary>, write a lambda

        return {
            "notes": [
                self.get_tags(note)[0].strip().replace("\\n", "") for note in result
            ]
        }

    @staticmethod
    def get_tags(text):
        return re.findall(r"<summary>(.*?)</summary>", text)
