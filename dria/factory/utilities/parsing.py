import re
from typing import Union, List
from json_repair import repair_json


def extract_backtick_label(text, label):
    """
    Extracts content between backticks with specified label

    Args:
        text (str): Input text containing backtick blocks
        label (str): Label to match (e.g., 'python', 'csv')

    Returns:
        list: List of content found between matching backtick blocks
    """
    import re

    # Create pattern for matching backticks with label
    pattern = f"```{label}(.*?)```"

    # Find all matches using regex
    # re.DOTALL flag allows . to match newlines
    matches = re.findall(pattern, text, re.DOTALL)

    # Strip whitespace from matches
    return [match.strip() for match in matches]


def get_tags(text: str, tag: str) -> List[str]:
    """Get all tags from the text.

    Args:
        text (str): The text to search for tags.
        tag (str): The tag to search for.

    Returns:
        list: The list of tags.
    """
    return re.findall(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)


def parse_json(text: Union[str, List]) -> Union[list[dict], dict, list[str]]:
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


def remove_text_between_tags(text: str, tag: str) -> Union[None, str]:
    """Remove the text between the given tags.

    Args:
        text (str): The text to remove the text between the tags from.
        tag (str): The tag to remove the text between.

    Returns:
        Union[None, str]: The text with the text between tags removed, or None if empty/None.
    """
    if not text or not tag:
        return None

    pattern = f"<{tag}>.*?</{tag}>"
    result = re.sub(pattern, "", text, flags=re.DOTALL).strip()
    return result if result else None


if __name__ == "__main__":
    text = "<json>{'key': 'value'}</json>"
    text2 = "```json{'key': 'value'}```"
    print(get_tags(text, "json"))
    print(parse_json(text2))
    t = "['Web Browser', 'Scheduling', 'Daily Life', 'File System', 'Communication', 'Note Taking', 'Productivity', 'Data Management', 'Security', 'Entertainment']"
    print(parse_json(t))

    t2 = """```python test ```"""
    t3 = "```test ```"
    print(extract_backtick_label(t2, "python"))
    print(extract_backtick_label(t3, ""))
