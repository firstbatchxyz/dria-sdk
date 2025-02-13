import logging
import os
from typing import Dict, List, Optional

from dria.datasets.utils import get_community_token
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.executor import TaskExecutor, Ping
from dria.manager import TaskManager
from dria.models import Task, TaskResult
from dria.request import RPCClient
from dria.workflow import WorkflowTemplate


class Dria:
    """
    Client SDK for interacting with the Dria distributed AI system.
    
    The Dria client provides a high-level interface for submitting AI tasks to the network,
    managing task execution, and retrieving results. It handles authentication, retries,
    and distributed task coordination.

    Example:
        >>> client = Dria(rpc_token="your_token") 
        >>> results = await client.generate(
        ...     instructions=[{"prompt": "Write a story"}],
        ...     workflow=Workflow,
        ...     models=[Model.GPT4O]
        ... )
    """

    def __init__(
            self,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the Dria client.

        Args:
            log_level: Logging level for the Dria client. Defaults to INFO.

        Raises:
            ValueError: If no valid authentication token is available
        """
        if hasattr(self, "_initialized"):
            return

        logging.getLogger("dria").setLevel(log_level)

        # Set up authentication
        rpc_token = get_community_token()

        if not rpc_token and not os.environ.get("DRIA_RPC_TOKEN"):
            raise ValueError("No RPC token provided. Set DRIA_RPC_TOKEN or pass rpc_token")

        # Initialize core components
        self.rpc = RPCClient(auth_token=rpc_token or os.environ.get("DRIA_RPC_TOKEN"))
        self.storage = Storage()
        self.kv = KeyValueQueue()

        # Create shared dependencies
        ping = Ping(self.storage, self.rpc, self.kv)
        task_manager = TaskManager(self.storage, self.rpc, self.kv)

        self.executor = TaskExecutor(
            ping=ping,
            rpc=self.rpc,
            storage=self.storage,
            kv=self.kv,
            task_manager=task_manager
        )

        self._initialized = True

    async def generate(
            self,
            instructions: List[Dict[str, any]],
            workflow: Type[WorkflowTemplate],
            models: str
    ) -> List[TaskResult]:
        """
        Generate tasks from instructions and execute workflows.

        Args:
            instructions: List of instruction dictionaries containing task parameters
            workflow: Workflow template class that builds the task workflow
            models: List of model identifiers to use for task execution

        Returns:
            List of TaskResult objects containing the generation results

        Raises:
            ValueError: If instructions or models are invalid
            RuntimeError: If task execution fails
        """
        if not instructions:
            raise ValueError("Instructions list cannot be empty")

        if not models:
            raise ValueError("Models list cannot be empty")

        tasks = [
            Task(workflow=workflow(**instruction), models=models)
            for instruction in instructions
        ]

        return await self.executor.execute(tasks)
