from pydantic import BaseModel
from typing import Dict, Any, Union


def schemas_match(
    schema1: Union[Dict[str, Any], BaseModel], schema2: Union[Dict[str, Any], BaseModel]
) -> bool:
    """
    Check if two schemas (Pydantic or Dict) match by comparing keys and types.

    :param schema1: First schema (Pydantic model or dict).
    :param schema2: Second schema (Pydantic model or dict).
    :return: True if schemas match, False otherwise.
    """

    def extract_properties(schema: Union[Dict[str, Any], BaseModel]) -> Dict[str, Any]:
        # Handle Pydantic model or model_fields
        if hasattr(schema, "model_fields"):
            s = {k: v.annotation for k, v in schema.model_fields.items()}
            del s["params"]
            return s
        # Handle plain dictionaries
        elif isinstance(schema, dict):
            return {k: type(v) for k, v in schema.items()}
        raise ValueError("Unsupported schema type. Must be Pydantic BaseModel or dict.")

    # Extract properties
    schema1_properties = extract_properties(schema1)
    schema2_properties = extract_properties(schema2)
    # Compare properties
    return schema1_properties == schema2_properties


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

    tm = TestModel(name="test", description="test", value=0.0)
    vm = ValidModel(name="valid", description="valid", value=2.0)
    em = ErrorModel(name="err", description="err", range=10)
    assert schemas_match(tm.model_json_schema(), vm.model_json_schema())
    assert not schemas_match(tm.model_json_schema(), em.model_json_schema())
