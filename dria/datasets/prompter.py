from typing import Type, Optional, Dict
from typing import List
from pydantic import BaseModel
from dria_workflows import WorkflowBuilder, Operator, Edge, Write
from dria.factory.utilities import parse_json
from dria.models import TaskResult
import re


def find_vars(prompt: str) -> List[str]:
    matches = re.findall(r"\{\{(.*?)}}", prompt, re.DOTALL)
    return matches


class Prompt:
    def __init__(
        self,
        prompt: str,
        schema: Type[BaseModel],
        input_map: Optional[Dict[str, str]] = None,
        max_tokens=1000,
    ) -> None:
        self.description = "prompt"
        self.prompt = prompt
        self.schema = schema
        self.input_map = input_map
        self.max_tokens = max_tokens

        self.variables = find_vars(self.prompt)
        if len(self.variables) == 0:
            raise RuntimeError(
                f"No variables found for instruction {self.prompt}. Try using double brackets."
            )

    def workflow(self, **kwargs):

        builder = WorkflowBuilder(**kwargs)
        builder.set_max_tokens(self.max_tokens)

        builder.generative_step(
            prompt=self.prompt,
            operator=Operator.GENERATION,
            schema=self.schema,
            outputs=[Write.new("response")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)

        builder.set_return_value("response")
        return builder.build()

    def callback(self, results: List[TaskResult]):
        return [self.schema(**parse_json(r.result)) for r in results]
