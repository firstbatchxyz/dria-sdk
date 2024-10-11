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
from typing import List


class WebMultiChoice(SingletonTemplate):
    """
    A workflow to answer multiple-choice questions using web search and evaluation.
    """

    def workflow(self, question: str, choices: List[str]) -> Workflow:
        """ """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(
            question=question, choices=choices, choices_back=choices
        )
        builder.set_max_time(200)
        builder.set_max_tokens(750)

        # Add a generative step using the prompt
        builder.generative_step(
            prompt="Learn more about {{choices}}. Use previous queries to avoid duplication: {{history}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[
                Pop.new("choices", required=True),
                GetAll.new("history", required=False),
            ],
            outputs=[Write.new("search"), Push.new("history")],
        )

        builder.generative_step(
            path=get_abs_path("mc_pick_url.md"),
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
            path=get_abs_path("mc_notes.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new("search_results", required=True),
                Read.new("question", required=True),
            ],
            outputs=[Push.new("notes")],
        )

        builder.generative_step(
            path=get_abs_path("mc_evaluate.md"),
            operator=Operator.GENERATION,
            inputs=[
                GetAll.new("notes", required=True),
                GetAll.new("choices_back", required=True),
                Read.new("question", required=True),
            ],
            outputs=[Write.new("evaluation")],
        )

        flow = [
            Edge(source="0", target="1"),
            Edge(source="1", target="2"),
            Edge(source="2", target="3", fallback="0"),
            Edge(
                source="3",
                target="4",
                fallback="0",
                condition=ConditionBuilder.build(
                    len(choices),
                    Expression.GREATER_THAN_OR_EQUAL,
                    Size.new("notes", required=True),
                    target_if_not="0",
                ),
            ),
            Edge(source="4", target="_end"),
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("evaluation")
        return builder.build()

    def parse_result(self, result):
        return {"answer": result[0].strip()}
