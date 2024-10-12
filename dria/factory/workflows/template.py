from abc import ABC, abstractmethod
from typing import List
from types import SimpleNamespace
from dria.models import TaskResult


class SingletonTemplate(ABC):
    """
    An abstract base class representing a singleton template.

    This class encapsulates the logic for creating a singleton template.
    """

    params: SimpleNamespace = SimpleNamespace()

    def __init__(self, **kwargs):
        super().__init__()
        self.params = SimpleNamespace(**kwargs)

    @abstractmethod
    def workflow(self, **kwargs):
        """
        The workflow method for the singleton template.
        Returns:

        """
        pass

    @abstractmethod
    def parse_result(self, result: List[TaskResult]):
        """
        The parse_result method for the singleton template.
        Args:
            result: The result to be parsed.
        Returns:
        """
        pass
