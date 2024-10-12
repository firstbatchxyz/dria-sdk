import re


def extract_tag(text: str) -> str:
    """Extracts the single tag enclosed in square brackets from the string.

    Args:
        text (str): The input string.

    Returns:
        str: The tag found in the string or None if no valid tag is found.
    """
    # Regex to match one of the allowed tags: factual, incorrect, or inconclusive
    pattern = r"\[(factual|incorrect|inconclusive)\]"

    # Search for the tag in the string
    match = re.search(pattern, text)

    return match.group(1) if match else None


if __name__ == "__main__":
    # Test the extract_tag function
    text1 = "The sky is blue. [factual]"
    text2 = "The moon is made of cheese. [incorrect]"
    text3 = "The earth is flat. [inconclusive]"
    text4 = "The sun is hot."

    print(extract_tag(text1))  # Output: "factual"
    print(extract_tag(text2))  # Output: "incorrect"
    print(extract_tag(text3))  # Output: "inconclusive"
    print(extract_tag(text4))  # Output: "None
