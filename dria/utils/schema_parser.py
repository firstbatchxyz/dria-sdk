import base64
import json
from typing import Any, Union, Type

from outlines_core.fsm.json_schema import build_regex_from_schema
from pydantic import BaseModel

from dria.utils.parsers import type_to_response_format_param


class SchemaParser:
    """Schema parser for different model providers."""

    @staticmethod
    def parse(model: type[BaseModel], provider: str) -> str:
        """
        Parse schema based on provider type.

        Args:
            model: Pydantic model to parse
            provider: Model provider (gemini, openai, ollama)

        Returns:
            Parsed schema string

        Raises:
            ValueError: If provider is not supported
        """
        parser_map = {
            "gemini": SchemaParser._parse_gemini,
            "openai": SchemaParser._parse_openai,
            "ollama": SchemaParser._parse_ollama,
            "openrouter": SchemaParser._parse_ollama,
        }

        if provider not in parser_map:
            raise ValueError(f"Unsupported provider: {provider}")

        return parser_map[provider](model)

    @staticmethod
    def _parse_gemini(model: Type[BaseModel]) -> str:
        """Parse schema for Gemini models."""

        def convert_type(field_type: Any) -> Union[dict, str]:
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ is list:
                    return {
                        "type": "ARRAY",
                        "items": {"type": convert_type(field_type.__args__[0])},
                    }
                elif field_type.__origin__ is dict:
                    return {
                        "type": "OBJECT",
                        "properties": {
                            "key": {"type": convert_type(field_type.__args__[0])},
                            "value": {"type": convert_type(field_type.__args__[1])},
                        },
                    }

            type_mapping = {
                str: "STRING",
                int: "INTEGER",
                float: "NUMBER",
                bool: "BOOLEAN",
            }
            return type_mapping.get(field_type, "STRING")

        properties = {}
        for name, field in model.__annotations__.items():
            if isinstance(field, type):
                properties[name] = {"type": convert_type(field)}
            else:
                properties[name] = convert_type(field)

        schema = {"type": "OBJECT", "properties": properties}

        return json.dumps(schema)

    @staticmethod
    def _parse_openai(model: Type[BaseModel]) -> str:
        """Parse schema for OpenAI models."""
        return json.dumps(type_to_response_format_param(model)["json_schema"]["schema"])

    @staticmethod
    def _parse_ollama(model: Type[BaseModel]) -> str:
        """Parse schema for Ollama models."""
        schema = json.dumps(model.model_json_schema())
        schedule = build_regex_from_schema(schema)
        schedule_bytes = schedule.encode("utf-8")
        base64_bytes = base64.b64encode(schedule_bytes)
        return base64_bytes.decode("utf-8")
