from pydantic import BaseModel
from typing import Dict, Any, Union, Type
import requests


def get_community_token() -> str:
    """Fetches and returns the URL from the API response."""
    response = requests.get("https://dkn.dria.co/auth/generate-token")
    if response.status_code == 200:
        return response.json()["data"][
            "auth_token"
        ]  # Assuming the response contains the URL as plain text
    else:
        raise Exception(f"Failed to fetch URL: {response.status_code}, {response.text}")


def schemas_match(
    input_schema: Union[Dict[str, Any], Type[BaseModel]],
    output_schema: Type[BaseModel],
) -> bool:
    """
    Check if two schemas (Pydantic or Dict) match by comparing keys and types.

    :param input_schema: Input schema (Pydantic model or dict).
    :param output_schema: Output schema (Pydantic model or dict).
    :return: True if schemas match, False otherwise.
    """

    if not isinstance(output_schema, type) or not issubclass(output_schema, BaseModel):
        raise ValueError("output_schema must be a Pydantic BaseModel.")

    if isinstance(input_schema, Dict):
        try:
            output_schema(**input_schema)
            return True
        except TypeError:
            return False

    def extract_properties(
        schema: Union[Dict[str, Any], Type[BaseModel]]
    ) -> Dict[str, Any]:
        # Handle Pydantic model or model_fields
        if hasattr(schema, "model_fields"):
            s = {k: v.annotation for k, v in schema.model_fields.items()}
            if "params" in s:
                del s["params"]
            return s
        raise ValueError("Unsupported schema type. Must be Pydantic BaseModel or dict.")

    # Extract properties
    input_properties = extract_properties(input_schema)
    output_properties = extract_properties(output_schema)
    # Compare properties
    for key, value_type in output_properties.items():
        if key not in input_properties:
            return False  # Missing required key
        if input_properties[key] != value_type:
            return False  # Type mismatch

    return True  # All required keys and types are valid


if __name__ == "__main__":

    class TestModel(BaseModel):
        name: str
        description: str
        value: float

    class ValidModel(BaseModel):
        name: str
        description: str
        value: float

    class ErrorModel(BaseModel):
        name: str
        description: str
        range: int

    assert schemas_match(TestModel, ValidModel)
    assert not schemas_match(TestModel, ErrorModel)
