import json
from typing import List

from dria.models.models import TaskInput
from dria.pipelines.step import Step
from dria.utils.task_utils import parse_json


def scatter_callback(step: Step) -> List[TaskInput]:
    """
    Scatter callback for 1-to-N operations.

    This callback takes a single input and distributes it to multiple outputs.

    Args:
        step (Step): The Step object containing input and output data.

    Returns:
        List[TaskInput]: A list of TaskInput objects for the next step.

    Raises:
        ValueError: If the output is not a valid JSON or not a list.
    """

    output_ = step.output[0].result

    try:
        parsed_output = parse_json(output_)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON output: {output_}")

    if not isinstance(parsed_output, list):
        raise ValueError(f"Output is not a list: {parsed_output}")

    return [
        TaskInput(**{key: item for key in step.next_step_input})
        for item in parsed_output
    ]


def broadcast_callback(step: Step) -> List[TaskInput]:
    """
    Broadcast callback for 1-to-N operations.

    This callback takes a single input and replicates it to multiple outputs.

    Args:
        step (Step): The Step object containing input and output data.

    Returns:
        List[TaskInput]: A list of TaskInput objects for the next step.

    Raises:
        ValueError: If the output is not a valid JSON or if there's an error during processing.
    """
    output_ = step.output[0].result
    try:
        parsed_output = parse_json(output_)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON output: {output_}")

    try:
        return [
            TaskInput(**{key: parsed_output for key in step.next_step_input})
            for _ in range(step.callback_params.get("n", 1))
        ]
    except Exception as e:
        raise ValueError(f"Error in broadcast_callback: {str(e)}")


def aggregation_callback(step: Step) -> TaskInput:
    """
    Aggregation callback for N-to-1 operations.

    This callback takes multiple inputs and combines them into a single output.

    Args:
        step (Step): The Step object containing input and output data.

    Returns:
        TaskInput: A single TaskInput object containing the aggregated data.

    Raises:
        ValueError: If the output is not a valid JSON or if there's an error during processing.
    """
    output_ = step.output[0].result
    try:
        parsed_output = parse_json(output_)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON output: {output_}")

    try:
        return TaskInput(**{step.next_step_input[0]: parsed_output})
    except Exception as e:
        raise ValueError(f"Error in aggregation_callback: {str(e)}")


def default_callback(step: Step) -> TaskInput:
    """
    Default callback for standard operations.

    This callback passes the input data directly to the output.

    Args:
        step (Step): The Step object containing input and output data.

    Returns:
        TaskInput: A single TaskInput object containing the output data.

    Raises:
        ValueError: If there's an error during processing.
    """
    output_ = step.output[0].result
    try:
        return TaskInput(result=output_)
    except Exception as e:
        raise ValueError(f"Error in default_callback: {str(e)}")
