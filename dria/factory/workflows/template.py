from abc import ABC, abstractmethod
from typing import List, Type, ClassVar
from types import SimpleNamespace
from dria.models import TaskResult
from pydantic import BaseModel


class SingletonTemplate(BaseModel, ABC):
    """
    An abstract base class representing a singleton template.

    This class encapsulates the logic for creating a singleton template.
    """

    params: SimpleNamespace = SimpleNamespace()
    OutputSchema: ClassVar[Type[BaseModel]]

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def preprocess(self):
        pass

    @classmethod
    def create(cls, **data):
        """Factory method to create an instance with validated input"""
        return cls(**data)

    @abstractmethod
    def workflow(self, **kwargs):
        """
        The workflow method for the singleton template.
        Returns:

        """
        pass

    @abstractmethod
    def callback(self, result: List[TaskResult]) -> List[Type[BaseModel]]:
        """
        The callback method for the singleton template.
        """
        pass
