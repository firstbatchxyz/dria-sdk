import json

from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from enum import Enum


class Message(BaseModel):
    role: str
    content: str


# Standard Format Models
class StandardLanguageModeling(BaseModel):
    """Simple text format for language modeling"""

    text: str


class StandardPromptOnly(BaseModel):
    """Standard prompt-only format"""

    prompt: str


class StandardPromptCompletion(BaseModel):
    """Standard prompt-completion format"""

    prompt: str
    completion: str


class StandardPreference(BaseModel):
    """Standard preference format for direct preference optimization"""

    prompt: str
    chosen: str
    rejected: str


class StandardUnpairedPreference(BaseModel):
    """Standard unpaired preference format"""

    prompt: str
    completion: str
    label: bool


# Conversational Format Models
class ConversationalLanguageModeling(BaseModel):
    """Conversational format for language modeling"""

    messages: List[Message]


class ConversationalPromptOnly(BaseModel):
    """Conversational format with prompt only"""

    prompt: List[Message]


class ConversationalPromptCompletion(BaseModel):
    """Conversational format with prompt and completion"""

    prompt: List[Message]
    completion: List[Message]


class ConversationalPreference(BaseModel):
    """Conversational format for preference learning"""

    prompt: List[Message]
    chosen: List[Message]
    rejected: List[Message]


class ConversationalUnpairedPreference(BaseModel):
    """Conversational format for unpaired preference learning"""

    prompt: List[Message]
    completion: List[Message]
    label: bool


class FormatType(str, Enum):
    # Standard formats
    STANDARD_LANGUAGE_MODELING = "standard_language_modeling"
    STANDARD_PROMPT_ONLY = "standard_prompt_only"
    STANDARD_PROMPT_COMPLETION = "standard_prompt_completion"
    STANDARD_PREFERENCE = "standard_preference"
    STANDARD_UNPAIRED_PREFERENCE = "standard_unpaired_preference"

    # Conversational formats
    CONVERSATIONAL_LANGUAGE_MODELING = "conversational_language_modeling"
    CONVERSATIONAL_PROMPT_ONLY = "conversational_prompt_only"
    CONVERSATIONAL_PROMPT_COMPLETION = "conversational_prompt_completion"
    CONVERSATIONAL_PREFERENCE = "conversational_preference"
    CONVERSATIONAL_UNPAIRED_PREFERENCE = "conversational_unpaired_preference"


class FieldMapping(BaseModel):
    """Configuration for mapping source data fields to target format fields"""

    # For standard formats
    text: Optional[str] = None  # for language modeling
    prompt: Optional[str] = None
    completion: Optional[str] = None
    chosen: Optional[str] = None
    rejected: Optional[str] = None
    label: Optional[str] = None

    user_message: Optional[str] = None
    assistant_message: Optional[str] = None
    system_message: Optional[str] = None


class ConversationMapping(BaseModel):
    """Configuration for mapping conversation object fields"""

    field: str  # field name for user messages in each turn (e.g., "instructor")
    conversation: FieldMapping


class DataFormatter:
    """Utility class for formatting training data into various formats"""

    FORMAT_SCHEMAS = {
        # Standard formats
        FormatType.STANDARD_LANGUAGE_MODELING: StandardLanguageModeling,
        FormatType.STANDARD_PROMPT_ONLY: StandardPromptOnly,
        FormatType.STANDARD_PROMPT_COMPLETION: StandardPromptCompletion,
        FormatType.STANDARD_PREFERENCE: StandardPreference,
        FormatType.STANDARD_UNPAIRED_PREFERENCE: StandardUnpairedPreference,
        # Conversational formats
        FormatType.CONVERSATIONAL_LANGUAGE_MODELING: ConversationalLanguageModeling,
        FormatType.CONVERSATIONAL_PROMPT_ONLY: ConversationalPromptOnly,
        FormatType.CONVERSATIONAL_PROMPT_COMPLETION: ConversationalPromptCompletion,
        FormatType.CONVERSATIONAL_PREFERENCE: ConversationalPreference,
        FormatType.CONVERSATIONAL_UNPAIRED_PREFERENCE: ConversationalUnpairedPreference,
    }

    REQUIRED_FIELDS = {
        FormatType.STANDARD_LANGUAGE_MODELING: {"text"},
        FormatType.STANDARD_PROMPT_ONLY: {"prompt"},
        FormatType.STANDARD_PROMPT_COMPLETION: {"prompt", "completion"},
        FormatType.STANDARD_PREFERENCE: {"prompt", "chosen", "rejected"},
        FormatType.STANDARD_UNPAIRED_PREFERENCE: {"prompt", "completion", "label"},
        FormatType.CONVERSATIONAL_LANGUAGE_MODELING: {
            "user_message",
            "assistant_message",
        },
        FormatType.CONVERSATIONAL_PROMPT_ONLY: {"user_message"},
        FormatType.CONVERSATIONAL_PROMPT_COMPLETION: {
            "user_message",
            "assistant_message",
        },
        FormatType.CONVERSATIONAL_PREFERENCE: {"user_message", "chosen", "rejected"},
        FormatType.CONVERSATIONAL_UNPAIRED_PREFERENCE: {
            "user_message",
            "completion",
            "label",
        },
    }

    @classmethod
    def validate_mapping(
        cls,
        format_type: FormatType,
        field_mapping: Union[FieldMapping, ConversationMapping],
    ) -> None:
        """Validate that the field mapping contains all required fields for the format"""
        required_fields = cls.REQUIRED_FIELDS[format_type]
        mapping_dict = field_mapping.model_dump(exclude_none=True)
        if field_mapping.conversation:
            missing_fields = required_fields - set(mapping_dict["conversation"].keys())
        else:
            missing_fields = required_fields - set(mapping_dict.keys())

        if missing_fields:
            raise ValueError(
                f"Missing required field mappings for format '{format_type}': {missing_fields}\n"
                f"Please provide mappings for these fields using get_format_info() to see requirements."
            )

    @classmethod
    def get_format_info(cls, format_type: FormatType) -> str:
        """Get information about the format and required field mappings"""
        schema = cls.FORMAT_SCHEMAS[format_type]
        required_fields = cls.REQUIRED_FIELDS[format_type]

        info = [
            f"\n=== {format_type.value} Format ===",
            f"\nDescription:",
            f"{schema.__doc__}",
            f"\nRequired Field Mappings:",
            f"{required_fields}",
            f"\nOutput Format:",
            f"{schema.model_json_schema()['properties']}",
        ]

        return "\n".join(info)

    @classmethod
    def format(
        cls,
        data: List[Dict],
        format_type: FormatType,
        field_mapping: Union[FieldMapping, ConversationMapping],
    ) -> List[Dict]:
        """Format a list of data items according to the specified format"""
        # Validate the field mapping
        cls.validate_mapping(format_type, field_mapping)

        formatted_data = []
        for item in data:
            try:
                # Standard formats
                if format_type == FormatType.STANDARD_LANGUAGE_MODELING:
                    formatted = {"text": item[field_mapping.text]}
                elif format_type == FormatType.STANDARD_PROMPT_ONLY:
                    formatted = {
                        "prompt": item[field_mapping.prompt],
                    }
                elif format_type == FormatType.STANDARD_PROMPT_COMPLETION:
                    formatted = {
                        "prompt": item[field_mapping.prompt],
                        "completion": item[field_mapping.completion],
                    }
                elif format_type == FormatType.STANDARD_PREFERENCE:
                    formatted = {
                        "prompt": item[field_mapping.prompt],
                        "chosen": item[field_mapping.chosen],
                        "rejected": item[field_mapping.rejected],
                    }
                elif format_type == FormatType.STANDARD_UNPAIRED_PREFERENCE:
                    formatted = {
                        "prompt": item[field_mapping.prompt],
                        "completion": item[field_mapping.completion],
                        "label": item[field_mapping.label],
                    }

                # Conversational formats
                elif format_type == FormatType.CONVERSATIONAL_LANGUAGE_MODELING:
                    if field_mapping.conversation:
                        dialogue_field, conv_mapping = (
                            field_mapping.field,
                            field_mapping.conversation,
                        )
                        messages = []

                        # Add system message if it exists in the mapping and data
                        if (
                            conv_mapping.system_message
                            and conv_mapping.system_message in item
                        ):
                            messages.append(
                                {
                                    "role": "system",
                                    "content": item[conv_mapping.system_message],
                                }
                            )

                        # Add conversation turns
                        for turn in item[dialogue_field]:
                            messages.extend(
                                [
                                    {
                                        "role": "user",
                                        "content": turn[conv_mapping.user_message],
                                    },
                                    {
                                        "role": "assistant",
                                        "content": turn[conv_mapping.assistant_message],
                                    },
                                ]
                            )
                        formatted = {"messages": messages}
                elif format_type == FormatType.CONVERSATIONAL_PROMPT_ONLY:
                    if field_mapping.conversation:
                        dialogue_field, conv_mapping = (
                            field_mapping.field,
                            field_mapping.conversation,
                        )
                        formatted = {"prompt": []}
                        # Add system message if exists
                        if (
                            conv_mapping.system_message
                            and conv_mapping.system_message in item
                        ):
                            formatted["prompt"].append(
                                {
                                    "role": "system",
                                    "content": item[conv_mapping.system_message],
                                }
                            )
                        # Add all user messages from dialogue
                        for turn in item[dialogue_field]:
                            formatted["prompt"].append(
                                {
                                    "role": "user",
                                    "content": turn[conv_mapping.user_message],
                                }
                            )

                elif format_type == FormatType.CONVERSATIONAL_PROMPT_COMPLETION:
                    if field_mapping.conversation:
                        dialogue_field, conv_mapping = (
                            field_mapping.field,
                            field_mapping.conversation,
                        )
                        formatted = {"prompt": [], "completion": []}
                        # Add system message if exists
                        if (
                            conv_mapping.system_message
                            and conv_mapping.system_message in item
                        ):
                            formatted["prompt"].append(
                                {
                                    "role": "system",
                                    "content": item[conv_mapping.system_message],
                                }
                            )
                        # Add all messages from dialogue
                        for turn in item[dialogue_field]:
                            formatted["prompt"].append(
                                {
                                    "role": "user",
                                    "content": turn[conv_mapping.user_message],
                                }
                            )
                            formatted["completion"].append(
                                {
                                    "role": "assistant",
                                    "content": turn[conv_mapping.assistant_message],
                                }
                            )

                elif format_type == FormatType.CONVERSATIONAL_PREFERENCE:
                    if field_mapping.conversation:
                        dialogue_field, conv_mapping = (
                            field_mapping.field,
                            field_mapping.conversation,
                        )
                        formatted = {"prompt": [], "chosen": [], "rejected": []}
                        # Add system message if exists
                        if (
                            conv_mapping.system_message
                            and conv_mapping.system_message in item
                        ):
                            formatted["prompt"].append(
                                {
                                    "role": "system",
                                    "content": item[conv_mapping.system_message],
                                }
                            )
                        # Add messages from dialogue
                        for turn in item[dialogue_field]:
                            formatted["prompt"].append(
                                {
                                    "role": "user",
                                    "content": turn[conv_mapping.user_message],
                                }
                            )
                            if conv_mapping.chosen in turn:
                                formatted["chosen"].append(
                                    {
                                        "role": "assistant",
                                        "content": turn[conv_mapping.chosen],
                                    }
                                )
                            if conv_mapping.rejected in turn:
                                formatted["rejected"].append(
                                    {
                                        "role": "assistant",
                                        "content": turn[conv_mapping.rejected],
                                    }
                                )

                elif format_type == FormatType.CONVERSATIONAL_UNPAIRED_PREFERENCE:
                    if field_mapping.conversation:
                        dialogue_field, conv_mapping = (
                            field_mapping.field,
                            field_mapping.conversation,
                        )
                        formatted = {
                            "prompt": [],
                            "completion": [],
                            "label": item[field_mapping.label],
                        }
                        # Add system message if exists
                        if (
                            conv_mapping.system_message
                            and conv_mapping.system_message in item
                        ):
                            formatted["prompt"].append(
                                {
                                    "role": "system",
                                    "content": item[conv_mapping.system_message],
                                }
                            )
                        # Add messages from dialogue
                        for turn in item[dialogue_field]:
                            formatted["prompt"].append(
                                {
                                    "role": "user",
                                    "content": turn[conv_mapping.user_message],
                                }
                            )
                            if conv_mapping.completion in turn:
                                formatted["completion"].append(
                                    {
                                        "role": "assistant",
                                        "content": turn[conv_mapping.completion],
                                    }
                                )

                # Validate the formatted data
                schema = cls.FORMAT_SCHEMAS[format_type]
                formatted_data.append(schema(**formatted).model_dump())

            except KeyError as e:
                raise KeyError(
                    f"Field mapping error: '{e}' not found in data item. Available fields: {list(item.keys())}"
                )

        return formatted_data


if __name__ == "__main__":
    # Example data with arbitrary field names
    data = [
        {
            "dialogue": [
                {
                    "question_text": "What are the advantages?",
                    "answer_good": "There are several advantages...",
                    "answer_bad": "The benefits include...",
                },
                {
                    "question_text": "What are the disadvantages?",
                    "answer_good": "The main disadvantages are...",
                    "answer_bad": "Some drawbacks include...",
                },
            ]
        }
    ]

    formatter = DataFormatter()

    # Define field mapping
    mapping = ConversationMapping(
        field="dialogue",  # the key containing the list of conversation turns
        conversation=FieldMapping(
            user_message="question_text", assistant_message="answer_good"
        ),
    )
    # Format data
    try:
        formatted = formatter.format(
            data, FormatType.CONVERSATIONAL_LANGUAGE_MODELING, mapping
        )
        print("\nFormatted data:")
        print(json.dumps(formatted, indent=2))
    except Exception as e:
        print(f"Error: {e}")
