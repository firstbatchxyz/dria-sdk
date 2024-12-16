import uuid
from unittest.mock import Mock, patch

import pytest
import json
import os
from typing import Dict, Any
from pydantic import BaseModel
import pandas as pd

from dria.datasets.base import DriaDataset
from dria.datasets.utils import schemas_match, get_community_token
from dria.db.database import DatasetDB
from dria.utils import FieldMapping, FormatType


# Test schema
class TestSchema(BaseModel):
    id: int
    text: str
    label: str


@pytest.fixture
def test_dataset():
    return DriaDataset(
        name="test_dataset",
        description="Test dataset",
        schema=TestSchema,
        db=DatasetDB(),
    )


@pytest.fixture
def sample_data():
    return [
        {"id": 1, "text": "test text 1", "label": "positive"},
        {"id": 2, "text": "test text 2", "label": "negative"},
    ]


def test_dataset_init(test_dataset):
    assert test_dataset.name == "test_dataset"
    assert test_dataset.description == "Test dataset"
    assert test_dataset._schema == TestSchema
    assert test_dataset.dataset_id is not None


def test_from_json(tmp_path):
    # Create temporary JSON file
    json_path = "test.json_"
    test_data = [
        {"id": 1, "text": "test", "label": "positive"},
        {"id": 2, "text": "test2", "label": "negative"},
    ]
    with open(json_path, "w") as f:
        json.dump(test_data, f)

    dataset = DriaDataset.from_json(
        f"test_json_{uuid.uuid4()}", "Test JSON dataset", TestSchema, str(json_path)
    )

    entries = dataset.get_entries(data_only=True)
    assert len(entries) == 2
    assert entries[0]["text"] == "test"


def test_from_csv(tmp_path):
    # Create temporary CSV file
    csv_path = tmp_path / "test.csv"
    with open(csv_path, "w") as f:
        f.write("id,text,label\n")
        f.write("1,test text,positive\n")
        f.write("2,test text 2,negative\n")

    dataset = DriaDataset.from_csv(
        f"test_csv_{uuid.uuid4()}", "Test CSV dataset", TestSchema, str(csv_path)
    )

    entries = dataset.get_entries(data_only=True)
    assert len(entries) == 2
    assert entries[0]["text"] == "test text"


def test_validate_entry(test_dataset):
    valid_entry = {"id": 1, "text": "test", "label": "positive"}
    validated = test_dataset.validate_entry(valid_entry)
    assert validated == valid_entry

    with pytest.raises(Exception):
        test_dataset.validate_entry({"invalid": "entry"})


def test_mutate(test_dataset, sample_data):
    test_dataset.db.add_entries(test_dataset.dataset_id, sample_data)

    field_name = "text_length"
    # Add new field
    new_values = {field_name: [len(entry["text"]) for entry in sample_data]}
    test_dataset.mutate(field_name, new_values, int)

    # Check schema update
    assert "text_length" in test_dataset.schema.model_fields

    # Check data update
    entries = test_dataset.get_entries(data_only=True)
    assert all("text_length" in entry for entry in entries)


def test_format_for_training(test_dataset, sample_data, tmp_path):
    test_dataset.reset()
    test_dataset.db.add_entries(test_dataset.dataset_id, sample_data)

    field_mapping = FieldMapping(
        text="text",
    )

    # Test JSON output
    output_path = str(tmp_path / "output")
    formatted = test_dataset.format_for_training(
        FormatType.STANDARD_LANGUAGE_MODELING, field_mapping, "json", output_path
    )

    assert len(formatted) == len(sample_data)
    assert os.path.exists(output_path + ".json")


def test_to_pandas(test_dataset, sample_data):
    test_dataset.reset()
    test_dataset.db.add_entries(test_dataset.dataset_id, sample_data)
    df = test_dataset.to_pandas()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_data)
    assert list(df.columns) == ["id", "text", "label"]


def test_remove_entry(test_dataset, sample_data):
    test_dataset.reset()
    test_dataset.db.add_entries(test_dataset.dataset_id, sample_data)
    entries = test_dataset.get_entries()
    test_dataset.remove_entry(entries[0]["entry_id"])

    updated_entries = test_dataset.get_entries()
    assert len(updated_entries) == len(sample_data) - 1


def test_remove_dataset(test_dataset, sample_data):
    test_dataset.db.add_entries(test_dataset.dataset_id, sample_data)
    test_dataset.remove_dataset()

    assert test_dataset.dataset_id is None
    assert test_dataset.name is None
    assert test_dataset.db is None


def test_get_community_token():
    # Test successful token fetch
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"auth_token": "test-token"}}
        mock_get.return_value = mock_response

        token = get_community_token()
        assert token == "test-token"
        mock_get.assert_called_once_with("https://dkn.dria.co/auth/generate-token")

    # Test failed token fetch
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with pytest.raises(Exception) as exc:
            get_community_token()
        assert str(exc.value) == "Failed to fetch URL: 404, Not found"


def test_schemas_match():
    # Test matching Pydantic models
    class Model1(BaseModel):
        name: str
        value: int

    class Model2(BaseModel):
        name: str
        value: int

    assert schemas_match(Model1, Model2)

    # Test non-matching models
    class Model3(BaseModel):
        name: str
        value: str

    assert not schemas_match(Model1, Model3)

    # Test dict input
    valid_dict = {"name": "test", "value": 1}

    assert schemas_match(valid_dict, Model1)

    # Test invalid dict
    invalid_dict = {"name": "test", "value": "string"}

    with pytest.raises(ValueError):
        schemas_match(invalid_dict, Model1)

    # Test model with extra params field
    class ModelWithParams(BaseModel):
        name: str
        value: int
        params: Dict[str, Any]

    assert schemas_match(Model1, ModelWithParams)

    # Test invalid schema type
    with pytest.raises(ValueError):
        schemas_match({"invalid": "schema"}, "not a model")
