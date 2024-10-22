import json
import re
from typing import Union, List


def get_tags(text: str, tag: str) -> List[str]:
    """Get all tags from the text.

    Args:
        text (str): The text to search for tags.
        tag (str): The tag to search for.

    Returns:
        list: The list of tags.
    """
    return re.findall(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)


def parse_json(text: Union[str, List]) -> Union[list[dict], dict]:
    """Parse the JSON text.

    Args:
        text (str): The text to parse.

    Returns:
        dict: JSON output.
    """

    def parse_single_json(result: str) -> dict:
        """Parse JSON text from a string, extracting from code blocks or <json> tags if present.

        Args:
            result (str): The text to parse.

        Returns:
            dict: Parsed JSON output.

        Raises:
            ValueError: If JSON cannot be parsed.
        """
        # Patterns to match code blocks with optional 'json' and <json> tags
        patterns = [
            r"```(?:JSON)?\s*(.*?)\s*```",  # Code block with or without 'json'
            r"<JSON>\s*(.*?)\s*</JSON>",  # <json>...</json> tags
        ]

        for pattern in patterns:
            match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
            if match:
                json_text = match.group(1)
                break
        else:
            json_text = result

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse JSON from result: {json_text}") from e

    if isinstance(text, list):
        return [parse_single_json(item) for item in text]
    else:
        return parse_single_json(text)


if __name__ == "__main__":
    text = "<json>{'key': 'value'}</json>"
    print(get_tags(text, "json"))
    print(parse_json(text))
    t = "['Web Browser', 'Scheduling', 'Daily Life', 'File System', 'Communication', 'Note Taking', 'Productivity', 'Data Management', 'Security', 'Entertainment']"
    print(parse_json(t))