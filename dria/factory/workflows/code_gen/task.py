from typing import List
from pydantic import BaseModel, Field
from dria_workflows import (
    Workflow,
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
)
from dria.factory.workflows.template import SingletonTemplate
from dria.models import TaskResult
import re

Language = [
    "python",
    "javascript",
    "java",
    "c++",
    "c",
    "rust",
    "haskell",
    "typescript",
    "go",
    "solidity",
    "ruby",
    "lua",
    "bash",
]


class CodeOutput(BaseModel):
    instruction: str = Field(..., description="The instruction used to generate code")
    language: str = Field(..., description="The programming language used")
    code: str = Field(..., description="The generated code")
    model: str = Field(..., description="Model used for generation")


class IteratedCodeOutput(CodeOutput):
    iterated_code: str = Field(..., description="The iterated version of the code")


class GenerateCode(SingletonTemplate):
    # Input fields
    instruction: str = Field(..., description="The instruction to generate code for")
    language: str = Field(
        ..., description="The programming language to generate code for"
    )

    # Output schema
    OutputSchema = CodeOutput

    def workflow(self) -> Workflow:
        builder = WorkflowBuilder(instruction=self.instruction, language=self.language)
        builder.set_max_tokens(750)

        builder.generative_step(
            prompt="You have been given the following instruction: "
            "{{instruction}}. Write clean, commented and robust code in {{language}}. Code: ",
            operator=Operator.GENERATION,
            outputs=[Write.new("code")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("code")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[CodeOutput]:
        return [
            CodeOutput(
                instruction=self.instruction,
                language=self.language,
                code=parser(r.result.strip(), self.language),
                model=r.model,
            )
            for r in result
        ]


class IterateCode(SingletonTemplate):
    # Input fields
    code: str = Field(..., description="The code to iterate over")
    instruction: str = Field(..., description="The instruction to generate code for")
    language: str = Field(
        ..., description="The programming language to generate code for"
    )

    # Output schema
    OutputSchema = IteratedCodeOutput

    def workflow(self) -> Workflow:
        builder = WorkflowBuilder(
            instruction=self.instruction, code=self.code, language=self.language
        )
        builder.set_max_tokens(750)

        builder.generative_step(
            prompt="Here is you previous code: {{code}}.\n Iterate your previous code based on the instruction: "
            "{{instruction}}. Write clean, commented and robust code in {{language}}. Code: ",
            operator=Operator.GENERATION,
            outputs=[Write.new("code")],
        )

        flow = [Edge(source="0", target="_end")]
        builder.flow(flow)
        builder.set_return_value("code")
        return builder.build()

    def callback(self, result: List[TaskResult]) -> List[IteratedCodeOutput]:
        return [
            IteratedCodeOutput(
                instruction=self.instruction,
                language=self.language,
                code=self.code,
                iterated_code=parser(r.result.strip(), self.language),
                model=r.model,
            )
            for r in result
        ]


def parser(code: str, language: str) -> str:
    """
    Extracts the code block for the specified language from the provided text.

    Args:
        code (str): The input string containing code blocks.
        language (Language): The programming language enum to extract.

    Returns:
        str: The extracted code.

    Raises:
        ValueError: If the specified code block for the language is not found.
    """
    pattern = rf"```{re.escape(language)}\s*\n?(.*?)```"
    match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        raise ValueError(
            f"Code block for language '{language}' not found in the provided text."
        )
