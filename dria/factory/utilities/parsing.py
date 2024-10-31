import re
from typing import Union, List

from json_repair import repair_json


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
        """Parse JSON text from a string, use json_repair to fix the JSON.
        Args:
            result (str): The text to parse.

        Returns:
            dict: Parsed JSON output.

        Raises:
            ValueError: If JSON cannot be parsed.
        """
        json_text = repair_json(result, return_objects=True)
        if json_text == "":
            raise ValueError(f"Could not parse JSON from result: {result}")
        return json_text

    if isinstance(text, list):
        return [parse_single_json(item) for item in text]
    else:
        return parse_single_json(text)


if __name__ == "__main__":
    text = "<json>{'key': 'value'}</json>"
    text2 = "```json{'key': 'value'}```"
    print(get_tags(text, "json"))
    print(parse_json(text2))
    t = "['Web Browser', 'Scheduling', 'Daily Life', 'File System', 'Communication', 'Note Taking', 'Productivity', 'Data Management', 'Security', 'Entertainment']"
    print(parse_json(t))
