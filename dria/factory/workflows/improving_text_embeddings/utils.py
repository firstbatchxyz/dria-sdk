import re
import json

import re
import json


def parse_json(result: str) -> dict:
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
        r"```(?:json)?\s*(.*?)\s*```",  # Code block with or without 'json'
        r"<json>\s*(.*?)\s*</json>",  # <json>...</json> tags
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


if __name__ == "__main__":
    print(parse_json('<json>```\n{"key": "value"}\n```</json>'))
