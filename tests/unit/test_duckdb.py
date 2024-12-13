import pytest
from dria.db.database import DatasetDB, DatabaseError


@pytest.fixture
def db():
    # Use temporary in-memory database for testing
    db = DatasetDB(":memory:")
    yield db
    db.close()


@pytest.fixture
def sample_entries():
    return [
        {"question": "Q1?", "answer": "A1", "score": 0.8},
        {"question": "Q2?", "options": ["A", "B", "C"], "correct": "B"},
        {"question": "Q3?", "options": ["A", "B", "C"], "correct": "C"},
    ]


def test_create_dataset(db):
    dataset_id = db.create_dataset("test_dataset", "test description")
    assert isinstance(dataset_id, int)
    assert dataset_id > 0

    datasets = db.get_datasets()
    assert len(datasets) == 1
    assert datasets[0]["name"] == "test_dataset"
    assert datasets[0]["description"] == "test description"


def test_add_entries(db, sample_entries):
    dataset_id = db.create_dataset("test_dataset")
    entry_ids = db.add_entries(dataset_id, sample_entries)

    assert len(entry_ids) == len(sample_entries)
    assert all(isinstance(id, int) for id in entry_ids)

    entries = db.get_dataset_entries(dataset_id)
    assert len(entries) == len(sample_entries)
    assert all("entry_id" in entry for entry in entries)
    assert all("data" in entry for entry in entries)


def test_remove_entry(db, sample_entries):
    dataset_id = db.create_dataset("test_dataset")
    entry_ids = db.add_entries(dataset_id, sample_entries)

    db.remove_entry(entry_ids[0], dataset_id)

    entries = db.get_dataset_entries(dataset_id)
    assert len(entries) == len(sample_entries) - 1

    with pytest.raises(DatabaseError):
        db.remove_entry(999999, dataset_id)  # Non-existent entry


def test_remove_dataset(db):
    dataset_id = db.create_dataset("test_dataset")
    db.remove_dataset(dataset_id)

    datasets = db.get_datasets()
    assert len(datasets) == 0

    with pytest.raises(DatabaseError):
        db.remove_dataset(999999)  # Non-existent dataset


def test_flush_datasets(db, sample_entries):
    dataset_id = db.create_dataset("test_dataset")
    db.add_entries(dataset_id, sample_entries)

    db.flush_datasets()

    datasets = db.get_datasets()
    assert len(datasets) == 0
    entries = db.get_dataset_entries(dataset_id)
    assert len(entries) == 0


def test_get_dataset_entries(db, sample_entries):
    dataset_id = db.create_dataset("test_dataset")
    db.add_entries(dataset_id, sample_entries)

    # Test with data_only=False (default)
    entries = db.get_dataset_entries(dataset_id)
    assert len(entries) == len(sample_entries)
    assert all(isinstance(entry["entry_id"], int) for entry in entries)
    assert all(isinstance(entry["data"], dict) for entry in entries)

    # Test with data_only=True
    entries = db.get_dataset_entries(dataset_id, data_only=True)
    assert len(entries) == len(sample_entries)
    assert all(isinstance(entry, dict) for entry in entries)
    assert "entry_id" not in entries[0]


def test_get_dataset_id_by_name(db):
    name = "test_dataset"
    dataset_id = db.create_dataset(name)

    retrieved_id = db.get_dataset_id_by_name(name)
    assert retrieved_id == dataset_id

    with pytest.raises(DatabaseError):
        db.get_dataset_id_by_name("nonexistent_dataset")


def test_add_fields_to_entries(db, sample_entries):
    dataset_id = db.create_dataset("test_dataset")
    db.add_entries(dataset_id, sample_entries)

    fields_and_values = {
        "difficulty": ["easy", "medium", "hard"],
        "review_status": ["pending", "reviewed", "pending"],
    }

    modified_count = db.add_fields_to_entries(dataset_id, fields_and_values)
    assert modified_count == len(sample_entries)

    entries = db.get_dataset_entries(dataset_id, data_only=True)
    assert all("difficulty" in entry for entry in entries)
    assert all("review_status" in entry for entry in entries)

    # Test with mismatched lengths
    with pytest.raises(DatabaseError):
        db.add_fields_to_entries(
            dataset_id, {"test_field": ["value1", "value2"]}  # Too few values
        )
