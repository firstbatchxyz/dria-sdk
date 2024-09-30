import json
import time
from typing import Optional, Dict, Any


class Storage:
    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}

    def set_value(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """
        Set a key-value pair in the local dictionary.
        If `ex` is provided, set an expiration time (in seconds) for the key.
        """
        expiry = time.time() + ex if ex else None
        self.data[key] = {"value": value, "expiry": expiry}

    def set_json(self, key: str, value: Any) -> None:
        """
        Set a JSON value for a key in the local dictionary.
        The value should be a Python object that can be serialized to JSON.
        """
        self.set_value(key, json.dumps(value))

    def get_value(self, key: str) -> Optional[str]:
        """
        Get the value of a key from the local dictionary.
        Returns the value if the key exists and hasn't expired, otherwise None.
        """
        if key in self.data:
            item = self.data[key]
            if item["expiry"] is None or item["expiry"] > time.time():
                return item["value"]
            else:
                del self.data[key]  # Remove expired key
        return None

    def update_value(self, key: str, field: str, value: Any) -> None:
        """
        Update the value of a key in the local dictionary.
        """
        current_value = json.loads(self.get_value(key) or "{}")
        if current_value:
            current_value[field] = value
            self.set_value(key, json.dumps(current_value))
        else:
            self.set_value(key, json.dumps({field: value}))

    def append_value(self, key: str, field: str, value: Any) -> None:
        """
        Append a value to a list in the local dictionary.
        """
        current_value = json.loads(self.get_value(key) or "{}")
        if current_value:
            if field not in current_value:
                current_value[field] = []
            current_value[field].append(value)
            self.set_value(key, json.dumps(current_value))
        else:
            self.set_value(key, json.dumps({field: [value]}))

    def remove_from_list(self, key: str, field: Optional[str], values: list) -> None:
        """
        Remove values from a list in the local dictionary.
        """
        current_value = json.loads(self.get_value(key) or "{}")
        if current_value:
            if field is None:
                current_value = list(set(current_value) - set(values))
            else:
                current_value[field] = list(set(current_value.get(field, [])) - set(values))
            self.set_value(key, json.dumps(current_value))
        else:
            raise ValueError(f"Key '{key}' does not exist in the local dictionary.")

    def delete_key(self, key: str) -> None:
        """
        Delete a key from the local dictionary.
        """
        if key in self.data:
            del self.data[key]

    def get_w_scan(self, pattern: str) -> list:
        """
        Get all keys matching the pattern.
        """
        import re
        regex = re.compile(pattern.replace("*", ".*"))
        return [key for key in self.data.keys() if regex.match(key)]


if __name__ == "__main__":
    redis_client = Storage()
    redis_client.set_value("test_key", "test_value", ex=5)  # Set to expire in 5 seconds
    print(redis_client.get_value("test_key"))  # Should print "test_value"
    time.sleep(6)  # Wait for 6 seconds
    print(redis_client.get_value("test_key"))
