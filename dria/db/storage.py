import asyncio
import json
import time
from typing import Optional, Dict, Any


class Storage:
    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def set_value(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        """
        Set a key-value pair in the local dictionary.
        If `ex` is provided, set an expiration time (in seconds) for the key.
        """
        async with self.lock:
            expiry = time.time() + ex if ex else None
            self.data[key] = {"value": value, "expiry": expiry}

    async def set_json(self, key: str, value: Any) -> None:
        """
        Set a JSON value for a key in the local dictionary.
        The value should be a Python object that can be serialized to JSON.
        """
        await self.set_value(key, json.dumps(value))

    async def get_value(self, key: str) -> Optional[str]:
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

    async def update_value(self, key: str, field: str, value: Any) -> None:
        """
        Update the value of a key in the local dictionary.
        """
        current_value = json.loads(await self.get_value(key) or "{}")
        if current_value:
            current_value[field] = value
            await self.set_value(key, json.dumps(current_value))
        else:
            await self.set_value(key, json.dumps({field: value}))

    async def append_value(self, key: str, field: str, value: Any) -> None:
        """
        Append a value to a list in the local dictionary.
        """
        current_value = json.loads(await self.get_value(key) or "{}")
        if current_value:
            if field not in current_value:
                current_value[field] = []
            current_value[field].append(value)
            await self.set_value(key, json.dumps(current_value))
        else:
            await self.set_value(key, json.dumps({field: [value]}))

    async def remove_from_list(
        self, key: str, field: Optional[str], values: list
    ) -> None:
        """
        Remove values from a list in the local dictionary.
        """
        current_value = json.loads(await self.get_value(key) or "{}")
        if current_value:
            if field is None:
                current_value = list(set(current_value) - set(values))
            else:
                current_value[field] = list(
                    set(current_value.get(field, [])) - set(values)
                )
            await self.set_value(key, json.dumps(current_value))
        else:
            raise ValueError(f"Key '{key}' does not exist in the local dictionary.")

    async def delete_key(self, key: str) -> None:
        """
        Delete a key from the local dictionary.
        """
        async with self.lock:
            if key in self.data:
                del self.data[key]

    async def get_w_scan(self, pattern: str) -> list:
        """
        Get all keys matching the pattern.
        """
        import re

        async with self.lock:
            regex = re.compile(pattern.replace("*", ".*"))
            return [key for key in self.data.keys() if regex.match(key)]
