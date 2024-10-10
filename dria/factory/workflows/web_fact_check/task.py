from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Push,
    Edge,
    Read,
    GetAll,
    Peek,
    Write,
    Pop,
    ConditionBuilder,
    Expression,
    Size,
)
from dria.factory.utilities import get_abs_path
from dria.factory.workflows.template import SingletonTemplate


class WebFactCheck(SingletonTemplate):

    def workflow(self, context: str) -> Workflow:
        """ """
        # Initialize the workflow with variables
        builder = WorkflowBuilder(context=context)
        builder.set_max_time(200)
        builder.set_max_tokens(750)

        # Add a generative step using the prompt
        builder.generative_step(
            path=get_abs_path("query.md"),
            operator=Operator.GENERATION,
            inputs=[
                Read.new("context", required=True),
                GetAll.new("previous_queries", required=False),
            ],
            outputs=[Push.new("previous_queries")],
        )

        builder.generative_step(
            prompt="{{previous_queries}}",
            operator=Operator.FUNCTION_CALLING,
            inputs=[Peek.new("previous_queries", 0, required=True)],
            outputs=[Write.new("search")],
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
            outputs=[Push.new("search_results")],
        )

        builder.generative_step(
            path=get_abs_path("contradict.md"),
            operator=Operator.GENERATION,
            inputs=[
                Pop.new("search_results", required=True),
                Read.new("context", required=True),
            ],
            outputs=[Push.new("contradictions")],
        )

        builder.generative_step(
            path=get_abs_path("evaluate.md"),
            operator=Operator.GENERATION,
            inputs=[GetAll.new("contradictions", required=True)],
            outputs=[Write.new("evaluation")],
        )

        flow = [
            Edge(source="0", target="1"),
            Edge(source="1", target="2", fallback="0"),
            Edge(source="2", target="3"),
            Edge(source="3", target="4", fallback="0"),
            Edge(
                source="4",
                target="5",
                condition=ConditionBuilder.build(
                    self.params.num_queries,
                    Expression.GREATER_THAN_OR_EQUAL,
                    Size.new("contradictions", required=True),
                    target_if_not="0",
                ),
            ),
            Edge(source="5", target="_end"),
        ]
        builder.flow(flow)

        # Set the return value of the workflow
        builder.set_return_value("evaluation")
        return builder.build()

    def parse_result(self, result):
        return {"graph": result[0]}
