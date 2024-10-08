import json
import random
import re
from typing import Any, Dict, List, Union
import time
from requests.exceptions import RequestException

import requests
from dria import constants


def sample_variable(variable: Dict[str, Any]) -> Any:
    """Sample a variable from the given dictionary.

    Args:
        variable (Dict[str, Any]): The variable to sample from.

    Raises:
        ValueError: If the variable type is not supported.

    Returns:
        Any: The sampled variable.
    """
    var_type = variable["type"]
    if var_type == "categorical":
        return random.choice(variable["values"])
    elif var_type == "numerical":
        return int(random.uniform(variable["values"]["min"], variable["values"]["max"]))
    elif var_type == "binary":
        return random.choice(["True", "False"])
    raise ValueError(f"Unsupported variable type: {var_type}")


def scrape_file(
    file: str, max_retries: int = 10, retry_delay: int = 10
) -> dict[str, Any]:
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://vectorhub-firstbatch.b-cdn.net/dkn/" + file
            )
            response.raise_for_status()
            return {"context": response.json()["data"]}
        except RequestException as e:
            if attempt == max_retries - 1:
                raise ValueError(
                    f"Failed to fetch file after {max_retries} attempts: {str(e)}"
                )
            print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)


def scrape(
    source: Any, chunk_size: int = 100, min_chunk_size: int = 28
) -> List[Dict[str, Any]]:
    """Scrape the given websites or fetch file.

    Args:
        source (Any): The source to scrape.
        min_chunk_size:
        chunk_size:

    Returns:
        List[Dict[str, Any]]: The scraped data.
    """
    chunk_size = chunk_size * 1024
    min_chunk_size = min_chunk_size * 1024

    if source["type"] == "file":
        context = [scrape_file(file) for file in source["path"]]
    else:
        token = constants.JINA_TOKEN
        headers = (
            {"Authorization": f"Bearer {token}", "X-With-Links-Summary": "true"}
            if token
            else None
        )

        context = [
            get_urls(
                requests.get(
                    f"https://r.jina.ai/{website.strip()}", headers=headers
                ).text
            )
            for website in (source["path"] or [])
        ]

    context_text = "\n".join(ctx["context"] for ctx in context)
    context_text = json.loads(json.dumps(context_text, ensure_ascii=False))

    chunks = [
        context_text[i : i + chunk_size]
        for i in range(0, len(context_text), chunk_size)
    ]

    if len(chunks) > 1 and len(chunks[-1].encode("utf-8")) < min_chunk_size:
        chunks[-2] += chunks[-1]
        chunks.pop()

    return chunks


def get_urls(text: str) -> Dict[str, Any]:
    """Get the URLs from the given text.

    Args:
        text (str): The text to extract the URLs from.

    Returns:
        Dict[str, Any]: The extracted URLs.
    """
    result = {"context": "", "urls": [], "labels": []}

    content_before_links = re.search(r"(.*?)(?=Links/Buttons:)", text, re.DOTALL)
    if content_before_links:
        content_before_links_text = content_before_links.group(1)
        result["context"] = re.sub(r"http\S+", "", content_before_links_text).strip()

    links_section = re.search(r"Links/Buttons:(.*)", text, re.DOTALL)
    if links_section:
        links = re.findall(r"- \[(.*?)\]\((https?://.*?)\)", links_section.group(1))
        result["urls"], result["labels"] = zip(*links) if links else ([], [])

    return result


def get_text_between_tags(text: str, tag: str) -> Union[None, str]:
    """Get the text between the given tags.

    Args:
        text (str): The text to extract the text between the tags from.
        tag (str): The tag to extract the text between.

    Returns:
        List[str]: The extracted text between the tags.
    """
    pattern = f"<{tag}>(.*?)(?:</{tag}>|$)"
    matches = [
        match.strip() for match in re.findall(pattern, text, re.DOTALL) if match.strip()
    ]
    if len(matches) == 0:
        return None
    return matches[0]


def remove_text_between_tags(text: str, tag: str) -> str:
    """Remove the text between the given tags.

    Args:
        text (str): The text to remove the text between the tags from.
        tag (str): The tag to remove the text between.

    Returns:
        str: The text with the text between the tags removed.
    """
    return re.sub(f"<{tag}>.*?</{tag}>", "", text, flags=re.DOTALL)


def parse_json(text: str) -> Dict:
    """Parse the JSON text.

    Args:
        text (str): The text to parse.

    Returns:
        dict: JSON output.
    """
    json_content = re.search(r"<JSON>(.*?)</JSON>", text, re.DOTALL)
    if not json_content:
        return {}

    json_text = re.sub(r"<[^>]+>", "", json_content.group(1)).strip()

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # If parsing fails, return an empty dictionary
        return {}


def parse_backstory(backstory_json: str) -> List[str]:
    """Parse the backstory JSON.

    Args:
        backstory_json (str): The JSON string containing the backstory.

    Returns:
        List[str]: The parsed backstory as a list of strings.
    """
    try:
        parsed = json.loads(backstory_json.replace("```json", ""))
        backstory = parsed.get("backstory", [])
        return backstory if isinstance(backstory, list) else [backstory]
    except json.JSONDecodeError:
        return [backstory_json]
