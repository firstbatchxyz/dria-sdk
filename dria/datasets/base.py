import csv
import json
import os
from typing import List, Dict, Optional, Type, Any, Literal, Union

import httpx
import pandas as pd
from datasets import Dataset as HFDataset
from datasets import load_dataset
from pydantic import BaseModel, create_model, ValidationError

from dria.db.database import DatasetDB
from dria.utils import FieldMapping, DataFormatter, FormatType, ConversationMapping
from dria.utils.deployer import HuggingFaceDeployer

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
        json_path: str,
    ) -> "DriaDataset":
        """Create dataset from JSON file."""
        db = DatasetDB()
        dataset = cls(name, description, schema, db)
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            # Handle both single dict and list of dicts
            entries = [data] if isinstance(data, dict) else data

            # Validate all entries against schema
            validated_data = []
            for entry in entries:
                try:
                    validated_data.append(schema(**entry).model_dump())
                except ValidationError as e:
                    print(f"Skipping invalid entry: {entry}. Error: {str(e)}")
                    continue

            if validated_data:
                dataset.db.add_entries(dataset.dataset_id, validated_data)

            return dataset

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        except IOError as e:
            raise ValueError(f"Error reading file {json_path}: {e}")

    @classmethod
    def from_csv(
        cls,
        name: str,
        description: str,
        schema: Type[BaseModel],
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
            csv_path: Path to CSV file
            delimiter: CSV delimiter (default: ',')
            has_header: Whether CSV has header row (default: True)

        Returns:
            DriaDataset instance
        """
        db = DatasetDB()
        dataset = cls(name, description, schema, db)

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = (
                    csv.DictReader(f, delimiter=delimiter)
                    if has_header
                    else csv.reader(f, delimiter=delimiter)
                )

                # If no header, use schema fields as keys
                if not has_header:
                    headers = list(schema.model_fields.keys())
                    reader = (dict(zip(headers, row)) for row in reader)

                entries = []
                for row in reader:
                    try:
                        # Validate against schema
                        validated_entry = schema(**row).model_dump()
                        entries.append(validated_entry)
                    except Exception as e:
                        print(f"Skipping invalid entry: {row}. Error: {str(e)}")
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
        dataset_id: str,
        schema: Type[BaseModel],
        mapping: Optional[Dict[str, str]] = None,
        split: str = "train",
    ) -> "DriaDataset":
        db = DatasetDB()
        hf_dataset = load_dataset(dataset_id)[split]

        mapped_data = []
        for item in hf_dataset:
            if mapping is not None:
                entry = {k: item[v] for k, v in mapping.items()}
            else:
                entry = item
            try:
                mapped_data.append(schema(**entry).model_dump())
            except ValidationError:
                raise ValueError(f"Failed to map entry to schema: {entry}")

        dataset = cls(name, description, schema, db)
        dataset.db.add_entries(dataset.dataset_id, mapped_data)
        return dataset

    def _update_schema(self, new_fields: Dict[str, Type]):
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
        self._update_schema({field_name: (field_type, ...)})

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

    def remove_entry(self, entry_id: int) -> None:
        """Remove an entry from the dataset."""
        self.db.remove_entry(entry_id, self.dataset_id)

    def reset(self) -> "DriaDataset":
        """Remove all entries from the dataset."""
        self.db.remove_all_entries(self.dataset_id)
        return self

    def remove_dataset(self) -> None:
        """Remove the dataset and all its entries from the database."""
        self.db.remove_dataset(self.dataset_id)
        self.dataset_id = None
        self.name = None
        self.db = None

    def to_pandas(self) -> pd.DataFrame:
        """Convert dataset to Pandas DataFrame."""
        return pd.DataFrame(self.get_entries(data_only=True))

    def to_jsonl(self, filepath: Optional[str] = None, force_ascii: bool = False):
        """Convert dataset to JSONL."""
        if filepath is None:
            filepath = self.name + ".jsonl"
        self.to_pandas().to_json(
            filepath, orient="records", lines=True, force_ascii=force_ascii
        )

    def to_json(self, filepath: Optional[str] = None, force_ascii: bool = False):
        """Convert dataset to JSON."""
        if filepath is None:
            filepath = self.name + ".json"
        self.to_pandas().to_json(
            filepath, orient="records", lines=False, force_ascii=force_ascii
        )

    def to_hf_dataset(self) -> HFDataset:
        """Convert dataset to HuggingFace dataset."""
        return HFDataset.from_pandas(self.to_pandas())

    def push_to_huggingface(
        self,
        token: str,
        repo_name: str,
        private: bool = False,
        rpc_token: Optional[str] = None,
    ) -> str:
        """
        Push dataset to HuggingFace Hub.

        Args:
            token: HuggingFace token
            repo_name: HuggingFace repository name
            private: Whether the dataset is private
            rpc_token: Dria RPC token

        Returns:
            URL of the dataset
        """
        try:
            url = HuggingFaceDeployer(token).deploy(
                self.to_hf_dataset(), repo_name, private
            )
        except Exception as e:
            raise RuntimeError(f"Failed to deploy dataset to HuggingFace Hub: {str(e)}")

        if private is False:
            try:
                if rpc_token is None:
                    try:
                        _id = self.db.get_dataset_id_by_name("rpc_url")
                        rpc_token = self.db.get_dataset_entries(
                            _id, data_only=True
                        )[0]["token"]
                    except (IndexError, KeyError) as e:
                        raise ValueError("Could not retrieve RPC token from database") from e

                response = httpx.post(
                    "https://dkn.dria.co/dashboard/supply/v0/logs/upload-dataset",
                    json={
                        "dataset_name": self.name,
                        "link": url,
                    },
                    headers={
                        "x-api-key": rpc_token
                    }
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to log dataset upload: {str(e)}")

        return url
