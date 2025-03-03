import csv
import json
import os
from typing import List, Dict, Optional, Any, Literal, Union

import datasets as hf_datasets
import httpx
import pandas as pd
from pydantic import ValidationError

from dria.db.database import DatasetDB
from dria.utilities import FieldMapping, DataFormatter, FormatType, ConversationMapping
from dria.utilities.deployer import HuggingFaceDeployer

OutputFormat = Literal["json", "jsonl", "huggingface"]


class DriaDataset:
    def __init__(
        self,
        collection: str,
        db: DatasetDB = None,
    ):
        """
        Initialize DriaDataset.

        Args:
            collection: The collection name of dataset
            db: Database connection
        """
        self.collection = collection
        self.db = db or DatasetDB()
        self.dataset_id = self._init_dataset()

    def _init_dataset(self) -> int:
        """Initialize or get existing dataset from DB."""
        datasets = self.db.get_datasets()
        for dataset in datasets:
            if dataset["name"] == self.collection:
                return dataset["dataset_id"]
        return self.db.create_dataset(self.collection)

    @classmethod
    def from_json(
        cls,
        name: str,
        json_path: str,
    ) -> "DriaDataset":
        """Create dataset from JSON file."""
        db = DatasetDB()
        dataset = cls(name, db)
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            # Handle both single dict and list of dicts
            entries = [data] if isinstance(data, dict) else data

            if entries:
                dataset.db.add_entries(dataset.dataset_id, entries)

            return dataset

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        except IOError as e:
            raise ValueError(f"Error reading file {json_path}: {e}")

    @classmethod
    def from_csv(
        cls,
        name: str,
        csv_path: str,
        delimiter: str = ",",
        headers: Optional[List[str]] = None,
        has_header: bool = True,
    ) -> "DriaDataset":
        """
        Create dataset from CSV file.

        Args:
            name: Name of the dataset
            csv_path: Path to CSV file
            delimiter: CSV delimiter (default: ',')
            headers: List of column headers if CSV has no header row
            has_header: Whether CSV has header row (default: True)

        Returns:
            DriaDataset instance
        """
        db = DatasetDB()
        dataset = cls(name, db)

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = (
                    csv.DictReader(f, delimiter=delimiter)
                    if has_header
                    else csv.reader(f, delimiter=delimiter)
                )

                # If no header, use provided headers as keys
                if not has_header:
                    if headers is None:
                        raise ValueError(
                            "Headers must be provided when has_header=False"
                        )
                    reader = (dict(zip(headers, row)) for row in reader)

                entries = []
                for row in reader:
                    try:
                        entries.append(row)
                    except Exception as e:
                        print(f"Skipping invalid entry: {row}. Error: {str(e)}")
                        continue

                # Add entries to database
                if entries:
                    dataset.db.add_entries(dataset.dataset_id, entries)

                return dataset

        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

    @classmethod
    def from_huggingface(
        cls,
        name: str,
        dataset_id: str,
        mapping: Optional[Dict[str, str]] = None,
        split: str = "train",
    ) -> "DriaDataset":
        db = DatasetDB()
        hf_dataset = hf_datasets.load_dataset(dataset_id)[split]

        mapped_data = []
        for item in hf_dataset:
            if mapping is not None:
                entry = {k: item[v] for k, v in mapping.items()}
            else:
                entry = item
            try:
                mapped_data.append(entry)
            except ValidationError:
                raise ValueError(f"Failed to map entry to schema: {entry}")

        dataset = cls(name, db)
        dataset.db.add_entries(dataset.dataset_id, mapped_data)
        return dataset

    def mutate(self, values: Dict[str, List[Any]]):
        """
        Add new field to all entries.

        Args:
            values: Values to add
        """
        # Add field to database entries
        self.db.add_fields_to_entries(self.dataset_id, values)

    def format_for_training(
        self,
        format_type: FormatType,
        field_mapping: Union[FieldMapping, ConversationMapping],
        output_format: OutputFormat,
        output_path: Optional[str] = None,
        hf_repo_id: Optional[str] = None,
    ) -> Union[List[Dict], hf_datasets.Dataset]:
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
            output_path = os.getcwd() + self.collection + "_" + format_type.name.lower()

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
            hf_dataset = hf_datasets.Dataset.from_list(formatted_data)

            # Push to hub if repo_id is provided
            hf_dataset.push_to_hub(
                hf_repo_id,
                private=True,
                commit_message=f"Update dataset: {self.collection}",
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
        self.collection = None
        self.db = None

    def to_pandas(self) -> pd.DataFrame:
        """Convert dataset to Pandas DataFrame."""
        return pd.DataFrame(self.get_entries(data_only=True))

    def to_jsonl(self, filepath: Optional[str] = None, force_ascii: bool = False):
        """Convert dataset to JSONL."""
        if filepath is None:
            filepath = self.collection + ".jsonl"
        self.to_pandas().to_json(
            filepath, orient="records", lines=True, force_ascii=force_ascii
        )

    def to_json(self, filepath: Optional[str] = None, force_ascii: bool = False):
        """Convert dataset to JSON."""
        if filepath is None:
            filepath = self.collection + ".json"
        self.to_pandas().to_json(
            filepath, orient="records", lines=False, force_ascii=force_ascii
        )

    def to_hf_dataset(self) -> hf_datasets.Dataset:
        """Convert dataset to HuggingFace dataset."""
        return hf_datasets.Dataset.from_pandas(self.to_pandas())

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
                        rpc_token = self.db.get_dataset_entries(_id, data_only=True)[0][
                            "token"
                        ]
                    except (IndexError, KeyError) as e:
                        raise ValueError(
                            "Could not retrieve RPC token from database"
                        ) from e

                response = httpx.post(
                    "https://dkn.dria.co/dashboard/supply/v0/logs/upload-dataset",
                    json={
                        "dataset_name": self.collection,
                        "link": url,
                    },
                    headers={"x-api-key": rpc_token},
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to log dataset upload: {str(e)}")

        return url
