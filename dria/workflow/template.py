from abc import ABC, abstractmethod
from typing import List, Type, ClassVar, Optional

from pydantic import BaseModel

from dria.workflow.config import WorkflowConfig
from dria.models import TaskResult


class WorkflowTemplate(BaseModel, ABC):
    """
    Base template for creating workflow definitions.

    Attributes:
        params: The workflow configuration parameters.
        OutputSchema: BaseModel for the workflow output.
    """

    params: Optional[WorkflowConfig] = None
    OutputSchema: ClassVar[Type[BaseModel]]

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __call__(self, **data):
        super().__init__(**data)

    def preprocess(self):
        """Hook for preprocessing before workflow execution"""
        pass

    @abstractmethod
    def build(self):
        """
        Define and build the workflow steps and logic.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def callback(self, result: List[TaskResult]) -> List[BaseModel]:
        """
        Process workflow results into output schema.
        Must be implemented by subclasses.
        """
        pass
