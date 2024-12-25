from pathlib import Path
import duckdb
import json
from typing import Dict, List, Any
from tqdm import tqdm  # type: ignore


def get_default_db_path():
    default_db_path = Path.home() / ".dria" / "datasets.duckdb"
    default_db_path.parent.mkdir(parents=True, exist_ok=True)
    return default_db_path


class DatasetDB:
    def __init__(self, db_path: str = get_default_db_path()):
        try:
            self.conn = duckdb.connect(db_path)
            self._initialize_tables()
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    def _initialize_tables(self) -> None:
        """Initialize tables for datasets and their entries."""
        try:
            # Datasets table to track different data generation runs
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_id INTEGER PRIMARY KEY,
                    name VARCHAR,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Entries table to store the actual data
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    entry_id INTEGER PRIMARY KEY,
                    dataset_id INTEGER,
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
                )
            """
            )
        except Exception as e:
            raise DatabaseError(f"Failed to initialize tables: {str(e)}")

    def create_dataset(self, name: str, description: str = "") -> int:
        """Create a new dataset."""
        try:
            result = self.conn.execute(
                """
                WITH new_id AS (
                    SELECT COALESCE(MAX(dataset_id) + 1, 1) as next_id 
                    FROM datasets
                )
                INSERT INTO datasets (dataset_id, name, description)
                SELECT next_id, ?, ?
                FROM new_id
                RETURNING dataset_id
            """,
                (name, description),
            ).fetchone()
            if result is None:
                raise DatabaseError("Failed to create dataset")
            return result[0]
        except Exception as e:
            raise DatabaseError(f"Failed to create dataset: {str(e)}")

    def add_entries(self, dataset_id: int, entries: List[Dict]) -> List[int]:
        """Add multiple entries to a dataset."""
        try:
            entry_ids = []
            for entry in tqdm(entries, desc="Adding entries to DB"):
                result = self.conn.execute(
                    """
                    WITH new_id AS (
                        SELECT COALESCE(MAX(entry_id) + 1, 1) as next_id 
                        FROM entries
                    )
                    INSERT INTO entries (entry_id, dataset_id, data)
                    SELECT next_id, ?, ?
                    FROM new_id
                    RETURNING entry_id
                """,
                    (dataset_id, json.dumps(entry)),
                ).fetchone()
                if result is None:
                    raise DatabaseError("Failed to add entry")
                entry_ids.append(result[0])

            # Update dataset's updated_at timestamp
            self.conn.execute(
                """
                UPDATE datasets 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE dataset_id = ?
            """,
                (dataset_id,),
            )

            return entry_ids
        except Exception as e:
            raise DatabaseError(f"Failed to add entries: {str(e)}")

    def remove_entry(self, entry_id: int, db_id: int) -> None:
        """Remove an entry from the database."""
        try:
            result = self.conn.execute(
                "SELECT 1 FROM entries WHERE entry_id = ? AND dataset_id = ?",
                (entry_id, db_id),
            ).fetchone()

            if not result:
                raise DatabaseError(
                    f"Entry with ID {entry_id} not found in dataset {db_id}"
                )

            self.conn.execute(
                "DELETE FROM entries WHERE entry_id = ? AND dataset_id = ?",
                (entry_id, db_id),
            )

            self.conn.execute(
                """
                UPDATE datasets 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE dataset_id = ?
                """,
                (db_id,),
            )
        except Exception as e:
            raise DatabaseError(f"Failed to remove entry: {str(e)}")

    def remove_all_entries(self, dataset_id: int) -> None:
        """Remove all entries from a dataset."""
        try:
            result = self.conn.execute(
                "SELECT 1 FROM datasets WHERE dataset_id = ?", (dataset_id,)
            ).fetchone()

            if not result:
                raise DatabaseError(f"Dataset with ID {dataset_id} not found")

            self.conn.execute("DELETE FROM entries WHERE dataset_id = ?", (dataset_id,))

            self.conn.execute(
                """
                UPDATE datasets 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE dataset_id = ?
                """,
                (dataset_id,),
            )
        except Exception as e:
            raise DatabaseError(f"Failed to remove all entries: {str(e)}")

    def remove_dataset(self, dataset_id: int) -> None:
        """Remove a dataset and all its entries from the database."""
        try:
            result = self.conn.execute(
                "SELECT 1 FROM datasets WHERE dataset_id = ?", (dataset_id,)
            ).fetchone()

            if not result:
                raise DatabaseError(f"Dataset with ID {dataset_id} not found")

            self.conn.execute("DELETE FROM entries WHERE dataset_id = ?", (dataset_id,))

            self.conn.execute(
                "DELETE FROM datasets WHERE dataset_id = ?", (dataset_id,)
            )
        except Exception as e:
            raise DatabaseError(f"Failed to remove dataset: {str(e)}")

    def flush_datasets(self) -> None:
        """Remove all datasets and their entries from the database."""
        try:
            self.conn.execute("DELETE FROM entries")
            self.conn.execute("DELETE FROM datasets")
            self.conn.execute("VACUUM ANALYZE")
        except Exception as e:
            raise DatabaseError(f"Failed to flush datasets: {str(e)}")

    def get_dataset_entries(self, dataset_id: int, data_only=False) -> List[Dict]:
        """Get all entries for a dataset."""
        try:
            results = self.conn.execute(
                """
                SELECT entry_id, data, created_at
                FROM entries
                WHERE dataset_id = CAST(? AS INTEGER)
                ORDER BY entry_id
                """,
                (dataset_id,),
            ).fetchall()
            if data_only:
                return [json.loads(row[1]) for row in results]
            return [
                {
                    "entry_id": row[0],
                    "data": json.loads(row[1]),
                    "created_at": str(row[2]),
                }
                for row in results
            ]
        except Exception as e:
            raise DatabaseError(f"Failed to fetch dataset entries: {str(e)}")

    def get_datasets(self) -> List[Dict[str, Any]]:
        """Get all datasets."""
        try:
            results = self.conn.execute(
                """
                SELECT dataset_id, name, description, created_at, updated_at
                FROM datasets
                ORDER BY created_at DESC
            """
            ).fetchall()

            return [
                {
                    "dataset_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": str(row[3]),
                    "updated_at": str(row[4]),
                }
                for row in results
            ]
        except Exception as e:
            raise DatabaseError(f"Failed to fetch datasets: {str(e)}")

    def get_dataset_id_by_name(self, name: str) -> int:
        """Get a dataset by its name."""
        datasets = self.get_datasets()
        for dataset in datasets:
            if dataset["name"] == name:
                return dataset["dataset_id"]

        raise DatabaseError(f"Dataset {name} not found")

    def add_fields_to_entries(
        self, dataset_id: int, fields_and_values: Dict[str, List[Any]]
    ) -> int:
        """
        Add multiple new fields to entries in a dataset with corresponding values.

        Args:
            dataset_id (int): The dataset to modify
            fields_and_values: Dict of field names and their corresponding value lists

        Returns:
            int: Number of entries modified
        """
        try:
            entries = self.conn.execute(
                """
                SELECT entry_id, data
                FROM entries
                WHERE dataset_id = ?
                ORDER BY entry_id
            """,
                (dataset_id,),
            ).fetchall()

            # Validate all value lists have correct length
            for field_name, values in fields_and_values.items():
                if len(entries) != len(values):
                    raise DatabaseError(
                        f"Number of values for field '{field_name}' ({len(values)}) "
                        f"does not match number of entries ({len(entries)})"
                    )

            # Update each entry with all its corresponding new values
            for i, (entry_id, data) in enumerate(entries):
                current_data = json.loads(data)
                for field_name, values in fields_and_values.items():
                    current_data[field_name] = values[i]

                self.conn.execute(
                    """
                    UPDATE entries 
                    SET data = ?
                    WHERE entry_id = ?
                """,
                    (json.dumps(current_data), entry_id),
                )

            # Update dataset's updated_at timestamp
            self.conn.execute(
                """
                UPDATE datasets 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE dataset_id = ?
            """,
                (dataset_id,),
            )

            return len(entries)
        except Exception as e:
            raise DatabaseError(f"Failed to add fields to entries: {str(e)}")

    def close(self):
        self.conn.close()


class DatabaseError(Exception):
    pass


# Example Usage
if __name__ == "__main__":
    import random

    try:
        db = DatasetDB()

        # Create a new dataset
        dataset_id = db.create_dataset(
            name=f"Test Run {random.randint(1, 100)}",
            description="First test generation run",
        )

        # Add some entries
        entries = [
            {"question": "Question 1?", "answer": "Answer 1", "score": 0.8},
            {"question": "Question 2?", "options": ["A", "B", "C"], "correct": "B"},
            {"question": "Question 3?", "options": ["A", "B", "C"], "correct": "C"},
            {
                "question": "Question 4?",
                "options": ["A", "B", "C"],
                "correct": "A",
                "score": 0.2,
            },
            {
                "question": "Question 5?",
                "options": ["A", "B", "C"],
                "correct": "B",
                "score": 0.2,
            },
        ]

        entry_ids = db.add_entries(dataset_id, entries)
        print(f"Added entries with IDs: {entry_ids}")

        # Get all datasets
        datasets = db.get_datasets()
        print("\nAll datasets:", json.dumps(datasets, indent=2))

        # Get entries for a specific dataset
        entries = db.get_dataset_entries(dataset_id)
        print("\nDataset entries:", json.dumps(entries, indent=2))

        fields_and_values = {
            "difficulty": ["easy", "medium", "hard", "medium", "easy"],
            "review_status": ["pending", "reviewed", "pending", "reviewed", "pending"],
            "score": [0.8, 0.9, 0.7, 0.85, 0.95],
        }

        modified_count = db.add_fields_to_entries(
            dataset_id=1, fields_and_values=fields_and_values
        )
        print(f"Modified {modified_count} entries")

        entries = db.get_dataset_entries(dataset_id)
        print("\nUpdated entries:", json.dumps(entries, indent=2))

    except DatabaseError as e:
        print(f"Database error: {str(e)}")
    finally:
        db.close()
