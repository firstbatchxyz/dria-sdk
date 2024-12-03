from typing import List, Dict, Optional, Type, Any, Literal, Union
from pydantic import BaseModel, create_model, ValidationError, Field
from datasets import load_dataset
from datasets import Dataset as HFDataset
import json
import os
from dria.models import Model
from dria.utils import FieldMapping, DataFormatter, FormatType, ConversationMapping
from dria.db.database import DatasetDB

OutputFormat = Literal["json", "jsonl", "huggingface"]


class DriaDataset:
    def __init__(
        self,
        name: str,
        description: str,
        schema: Type[BaseModel],
        db: DatasetDB = None,
    ):
        """
        Initialize DriaDataset.

        Args:
            name: Name of the dataset
            description: Description of the dataset
            schema: Pydantic model defining the structure of entries
            db: Database connection
        """
        self.name = name
        self.description = description
        self._schema = schema
        self.db = db or DatasetDB()
        self.dataset_id = self._init_dataset()

    def _init_dataset(self) -> int:
        """Initialize or get existing dataset from DB."""
        datasets = self.db.get_datasets()
        for dataset in datasets:
            if dataset["name"] == self.name:
                return dataset["dataset_id"]
        return self.db.create_dataset(self.name, self.description)

    @classmethod
    def from_json(
        cls,
        name: str,
        description: str,
        schema: Type[BaseModel],
        db: DatasetDB,
        json_path: str,
    ) -> "DriaDataset":
        """Create dataset from JSON file."""
        dataset = cls(name, description, schema, db)
        with open(json_path, "r") as f:
            data = json.load(f)
        # Validate data against schema
        validated_data = []
        for entry in data:
            try:
                entry = json.loads(entry)
                validated_data.append(schema(**entry).model_dump())
            except ValidationError as e:
                print(f"Validation error: {e}. Skipping: {entry}")
        dataset.db.add_entries(dataset.dataset_id, validated_data)
        return dataset

    @classmethod
    def from_csv(
        cls,
        name: str,
        description: str,
        schema: Type[BaseModel],
        db: DatasetDB,
        csv_path: str,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> "DriaDataset":
        """
        Create dataset from CSV file.

        Args:
            name: Name of the dataset
            description: Description of the dataset
            schema: Pydantic model defining the structure
            db: Database connection
            csv_path: Path to CSV file
            delimiter: CSV delimiter (default: ',')
            has_header: Whether CSV has header row (default: True)

        Returns:
            DriaDataset instance
        """
        dataset = cls(name, description, schema, db)

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                # Read header if exists
                if has_header:
                    headers = f.readline().strip().split(delimiter)
                else:
                    # If no header, use schema field names in order
                    headers = list(schema.model_fields.keys())

                # Read and parse data
                entries = []
                for line in f:
                    values = line.strip().split(delimiter)
                    if len(values) != len(headers):
                        continue  # Skip malformed lines

                    # Create dict from headers and values
                    entry = {
                        headers[i]: values[i].strip("\"'") for i in range(len(headers))
                    }

                    try:
                        # Validate against schema
                        validated_entry = schema(**entry).model_dump()
                        entries.append(validated_entry)
                    except Exception as e:
                        print(f"Skipping invalid entry: {entry}. Error: {str(e)}")
                        continue

                # Add validated entries to database
                if entries:
                    dataset.db.add_entries(dataset.dataset_id, entries)

                return dataset

        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

    @classmethod
    def from_huggingface(
        cls,
        name: str,
        description: str,
        schema: Type[BaseModel],
        db: DatasetDB,
        dataset_id: str,
        mapping: Dict[str, str],
        split="train",
    ) -> "DriaDataset":
        """Create dataset from HuggingFace dataset."""
        dataset = cls(name, description, schema, db)
        # Map HF dataset fields to schema fields
        mapped_data = []
        hf_dataset = load_dataset(dataset_id)[split]

        for item in hf_dataset:
            entry = {
                schema_field: item[hf_field]
                for schema_field, hf_field in mapping.items()
            }
            mapped_data.append(schema(**entry).model_dump())
        dataset.db.add_entries(dataset.dataset_id, mapped_data)
        return dataset

    def update_schema(self, new_fields: Dict[str, Type]):
        """
        Update schema with new fields.

        Args:
            new_fields: Dictionary of field names and their types
        """
        # TODO: work with nested pydantic classes
        current_fields = (
            {
                name: (field.annotation, field.default)
                for name, field in self._schema.model_fields.items()
            }
            if self._schema
            else {}
        )

        # Merge current fields with new fields
        all_fields = {**current_fields, **new_fields}

        # Create new schema
        self._schema = create_model(f"{self.name}Schema", **all_fields)

    @property
    def schema(self) -> Type[BaseModel]:
        """Get current schema."""
        return self._schema

    def validate_entry(self, entry: Dict) -> Dict:
        """Validate entry against current schema."""
        if self._schema is None:
            return entry
        return self._schema(**entry).model_dump()

    def mutate(
        self, field_name: str, values: Dict[str, List[Any]], field_type: Type = None
    ):
        """
        Add new field to all entries and update schema.

        Args:
            field_name: Name of the new field
            values: Values to add
            field_type: Type of the field (optional, will be inferred if not provided)
        """
        # Add field to database entries
        self.db.add_fields_to_entries(self.dataset_id, values)

        # Infer type if not provided
        if field_type is None:
            field_type = type(values[0]) if values else Any

        # Update schema
        self.update_schema({field_name: (field_type, ...)})

    def format_for_training(
        self,
        format_type: FormatType,
        field_mapping: Union[FieldMapping, ConversationMapping],
        output_format: OutputFormat,
        output_path: Optional[str] = None,
        hf_repo_id: Optional[str] = None,
    ) -> Union[List[Dict], HFDataset]:
        """
        Format dataset for training and save/upload in specified format.

        Args:
            format_type: Type of formatting to apply
            field_mapping: Mapping of fields for formatting
            output_format: Format to save data ("json", "jsonl", or "huggingface")
            output_path: Path to save the output file (required for json/jsonl)
            hf_repo_id: HuggingFace repository ID (required for huggingface format)

        Returns:
            Formatted data as list of dicts or HuggingFace dataset
        """
        entries = self.db.get_dataset_entries(self.dataset_id, data_only=True)
        formatter = DataFormatter()
        formatted_data = formatter.format(entries, format_type, field_mapping)

        if not output_path:
            output_path = os.getcwd() + self.name + "_" + format_type.name.lower()

        if output_format == "json":
            output_path += ".json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, indent=2, ensure_ascii=False)

        elif output_format == "jsonl":
            output_path += ".jsonl"
            with open(output_path, "w", encoding="utf-8") as f:
                for item in formatted_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

        elif output_format == "huggingface":
            if not hf_repo_id:
                raise ValueError("hf_repo_id is required for HuggingFace format")

            # Convert to HuggingFace dataset
            hf_dataset = HFDataset.from_list(formatted_data)

            # Push to hub if repo_id is provided
            hf_dataset.push_to_hub(
                hf_repo_id, private=True, commit_message=f"Update dataset: {self.name}"
            )
            return hf_dataset

        return formatted_data

    def get_entries(self, data_only=False) -> List[Dict]:
        """Get all entries in the dataset."""
        return self.db.get_dataset_entries(self.dataset_id, data_only)


if __name__ == "__main__":

    class QuestionSchema(BaseModel):
        question: str = Field(..., description="The question text")
        options: Dict[str, str] = Field(..., description="Question options")
        correct_answer: str = Field(..., description="The correct answer")
        model_answer: Optional[str] = Field(None, description="Model's answer")
        model_reason: Optional[str] = Field(None, description="Model's reasoning")
        validation_score: Optional[str] = Field(None, description="Validation score")

        class Config:
            protected_namespaces = ()  # This removes the warning about model_ prefix

    # Usage:
    qs = QuestionSchema(
        question="",
        options={"question": "What is your name?"},
        correct_answer="",
        model_answer="",
        model_reason="",
        validation_score="",
    )

    # Print fields
    for k, v in qs.model_fields.items():
        print(k, v)

    # Usage example:
    async def main():
        dataset = DriaDataset(
            name="Medical Questions v1",
            description="Medical questions with model validations",
            schema=QuestionSchema,
        )

        # Generate data
        await dataset.generate_data(
            singleton=MedicalQA(),
            models=[Model.LLAMA_3_1_70B_OR, Model.GPT4O],
            instructions=instructions,
        )

        # Mutate dataset
        new_scores = [1, 2, 3, 4, 5]  # One for each entry
        dataset.mutate("new_score", new_scores)

        # Format for training
        formatted_data = dataset.format_for_training(
            format_type=FormatType.STANDARD_UNPAIRED_PREFERENCE,
            field_mapping=FieldMapping(
                prompt="question", completion="model_answer", label="validation_score"
            ),
            score_threshold=3,
        )
