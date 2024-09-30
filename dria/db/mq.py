import threading
from collections import deque
from typing import Any, Dict, Optional


class KeyValueQueue:
    def __init__(self):
        """
        Initialize the KeyValueQueue with an empty dictionary and a threading lock.
        """
        self.queue: Dict[str, deque] = {}
        self.lock = threading.Lock()

    def push(self, key: str, value: Any) -> None:
        """
        Add a value to the queue associated with the given key.
        If the key doesn't exist, create a new queue for it.
        """
        with self.lock:
            if key not in self.queue:
                self.queue[key] = deque()
            self.queue[key].append(value)

    def pop(self, key: str) -> Optional[Any]:
        """
        Remove and return the first item in the queue for the given key.
        If the key doesn't exist or the queue is empty, return None.
        """
        if key in self.queue and self.queue[key]:
            return self.queue[key].popleft()
        return None

    def peek(self, key: str) -> Optional[Any]:
        """
        Return the first item in the queue for the given key without removing it.
        If the key doesn't exist or the queue is empty, return None.
        """
        with self.lock:
            if key in self.queue and self.queue[key]:
                return self.queue[key][0]
            return None

    def is_empty(self, key: str) -> bool:
        """
        Check if the queue for the given key is empty or doesn't exist.
        """
        return key not in self.queue or len(self.queue[key]) == 0

    def size(self, key: str) -> int:
        """
        Return the number of items in the queue for the given key.
        If the key doesn't exist, return 0.
        """
        return len(self.queue.get(key, []))

    def clear(self, key: str) -> None:
        """
        Remove all items from the queue associated with the given key.
        """
        with self.lock:
            if key in self.queue:
                self.queue[key].clear()

    def keys(self) -> list[str]:
        """
        Return a list of all keys in the KeyValueQueue.
        """
        return list(self.queue.keys())
