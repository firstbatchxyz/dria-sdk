import json
import logging
import re
from typing import List, Union, Dict, Any

from dria_workflows import Workflow
from json_repair import repair_json

from dria.constants import RETURN_DEADLINE
from dria.models import Task
from dria.models.enums import (
    FunctionCallingModels,
    OpenAIModels,
    OllamaModels,
    CoderModels,
    GeminiModels,
    OpenRouterModels,
    SmallModels,
    MidModels,
    LargeModels,
    ReasoningModels,
)

logger = logging.getLogger(__name__)


class Helper:
    @staticmethod
    def is_task_valid(task: Task, current_time: int) -> bool:
        """
        Check if task is within deadline.

        Args:
            task: Task to validate
            current_time: Current timestamp

        Returns:
            bool: True if valid
        """
        task_deadline = int(task.deadline)
        if task_deadline == 0:
            logger.debug(f"Task {task.id} has no deadline. Skipping.")
            return False
        if (current_time - task_deadline) > RETURN_DEADLINE:
            logger.debug(f"Task {task.id} deadline exceeded. Skipping.")
            return False
        return True

    @staticmethod
    async def check_function_calling_models(tasks: List[Task]) -> None:
        """
        Validate models for function calling tasks.

        Args:
            tasks: Task to validate

        Raises:
            ValueError: If no supported models found
        """
        for task in tasks:
            if isinstance(task.workflow, Workflow):
                has_function_calling = any(
                    t.operator == "function_calling" for t in task.workflow.tasks
                )
            else:
                has_function_calling = any(
                    t.get("operator") == "function_calling"
                    for t in task.workflow.get("tasks", [])
                )
            supported_models = set(model.value for model in FunctionCallingModels)

            model_list = []
            for model in task.models:
                if model == "openai":
                    model_list.extend(model.value for model in OpenAIModels)
                elif model == "ollama":
                    model_list.extend(model.value for model in OllamaModels)
                elif model == "coder":
                    model_list.extend(model.value for model in CoderModels)
                elif model == "gemini":
                    model_list.extend(model.value for model in GeminiModels)
                elif model == "openrouter":
                    model_list.extend(model.value for model in OpenRouterModels)
                elif model == "small":
                    model_list.extend(model.value for model in SmallModels)
                elif model == "mid":
                    model_list.extend(model.value for model in MidModels)
                elif model == "large":
                    model_list.extend(model.value for model in LargeModels)
                elif model == "reasoning":
                    model_list.extend(model.value for model in ReasoningModels)
                else:
                    model_list.append(model)

            filtered_models = model_list
            if has_function_calling:
                filtered_models = [
                    model for model in model_list if model in supported_models
                ]

                for model in model_list:
                    if model not in supported_models:
                        logger.warning(
                            f"Model '{model}' not supported for function calling and will be removed."
                        )

                if not filtered_models:
                    supported_model_names = [
                        model.name for model in FunctionCallingModels
                    ]
                    raise ValueError(
                        f"No supported function calling models found for task. "
                        f"Supported models: {', '.join(supported_model_names)}"
                    )

            task.models = filtered_models

    @staticmethod
    def parse_json(
        text: Union[str, List[str]]
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parse JSON from a string or a list of strings, handling different text formats.

        Supports:
        - Raw JSON
        - JSON in code blocks (```)
        - JSON in <JSON> tags
        - Lists of JSON strings

        Args:
            text (Union[str, List[str]]): Text or list of texts containing JSON.

        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: Parsed JSON as dict or list of dicts.

        Raises:
            ValueError: If JSON parsing fails.
        """

        def _parse_single_json(raw_str: str) -> Dict[str, Any]:
            """
            Extract valid JSON from raw_str, handling embedded code blocks or <JSON> tags.

            Args:
                raw_str (str): A string potentially containing embedded JSON.

            Returns:
                Dict[str, Any]: The parsed JSON object.

            Raises:
                ValueError: If JSON is invalid or irreparable.
            """
            # Possible patterns for extracting JSON
            patterns = [
                r"```(?:JSON)?\s*(.*?)\s*```",
                r"<JSON>\s*(.*?)\s*</JSON>",
            ]

            json_text = raw_str
            # Attempt regex extraction for code block or <JSON> tag
            for pattern in patterns:
                match = re.search(pattern, raw_str, re.DOTALL | re.IGNORECASE)
                if match:
                    json_text = match.group(1)
                    break

            # Attempt repair and parse
            try:
                return repair_json(json_text, return_objects=True)
            except json.JSONDecodeError as e:
                # Raise an error if the repair fails
                raise ValueError(f"Invalid JSON format: {json_text}") from e

        if isinstance(text, list):
            # If we receive a list of JSON strings, parse each individually
            return [_parse_single_json(item) for item in text]
        else:
            # Otherwise parse the single input
            return _parse_single_json(text)
