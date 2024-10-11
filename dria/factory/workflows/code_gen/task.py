from dria_workflows import Workflow, WorkflowBuilder, Operator, Write, Edge
from dria.factory.workflows.template import SingletonTemplate
from typing import Dict, List, Literal
import re

Language = Literal[
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


def parser(code: str, language: Language) -> str:
    """
    Extracts the code block for the specified language from the provided text.

    Args:
        code (str): The input string containing code blocks.
        language (Language): The programming language enum to extract.

    Returns:
        Dict[str, Any]: A dictionary containing the extracted code.

    Raises:
        ValueError: If the specified code block for the language is not found.
    """
    # Construct the regex pattern using the language's value
    pattern = rf"```{re.escape(language)}\s*\n?(.*?)```"

    # Search for the pattern in the input code
    match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)

    if match:
        extracted_code = match.group(1).strip()
        return extracted_code
    else:
        raise ValueError(
            f"Code block for language '{language}' not found in the provided text."
        )


class GenerateCode(SingletonTemplate):

    def workflow(self, instruction: str, language: Language) -> Workflow:
        """

        :param instruction: The instruction to generate code for.
        :param language: The programming language to generate code for.
        :return:
        """
        self.params.instruction = instruction
        self.params.language = language
        builder = WorkflowBuilder(instruction=instruction, language=language)
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

    def parse_result(self, result: List[str]) -> Dict[str, str]:
        return {
            "instruction": self.params.instruction,
            "language": self.params.language,
            "code": parser(result[0].strip(), self.params.language),
        }


class IterateCode(SingletonTemplate):

    def workflow(self, code: str, instruction: str, language: Language) -> Workflow:
        """
        :param code: The code to iterate over.
        :param instruction: The instruction to generate code for.
        :param language: The programming language to generate code for.
        :return:
        """
        self.params.instruction = instruction
        self.params.language = language
        self.params.code = code
        builder = WorkflowBuilder(instruction=instruction, code=code, language=language)
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

    def parse_result(self, result: List[str]) -> Dict[str, str]:
        return {
            "instruction": self.params.instruction,
            "language": self.params.language,
            "iterated_code": parser(result[0].strip(), self.params.language),
            "code": self.params.code,
        }
