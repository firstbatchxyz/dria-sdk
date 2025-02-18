import logging
import os
from typing import Dict, List, Type, Optional, Union, Any

from dria.models import Model
from dria.datasets.utils import get_community_token
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.executor import TaskExecutor, Ping
from dria.manager import TaskManager
from dria.models import Task, TaskResult
from dria.request import RPCClient
from dria.workflow import WorkflowTemplate
from dria.workflow.factory import Simple


class Dria:
    """
    Client SDK for interacting with the Dria distributed AI system.

    The Dria client provides a high-level interface for submitting AI tasks to the network,
    managing task execution, and retrieving results. It handles authentication, retries,
    and distributed task coordination.

    Example:
        >>> client = Dria(rpc_token="your_token")
        >>> results = await client.generate(
        ...     variables=[{"prompt": "Write a story"}],
        ...     workflow=Workflow,
        ...     models=Model.GPT4O
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
            raise ValueError(
                "No RPC token provided. Set DRIA_RPC_TOKEN or pass rpc_token"
            )

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
            task_manager=task_manager,
        )

        self._initialized = True
    async def generate(
        self,
        inputs: Union[List[Dict[str, Any]], Dict[str, Any], str],
        workflow: Optional[Type[WorkflowTemplate]] = None,
        models: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        max_steps: Optional[int] = None,
        max_time: Optional[int] = None,
    ) -> List[TaskResult]:
        """
        Generate tasks from instructions and execute workflows.

        Args:
            inputs: List of instruction dictionaries, single dictionary, or string containing task parameters.
                      Must not be empty.
            workflow: Optional workflow template class that builds the task workflow.
                     Defaults to Simple workflow if not provided.
            models: Optional model identifier(s) to use for task execution.
                   Can be a single model string or list of models.
                   Defaults to GPT-4O if not provided.
            max_tokens: Optional maximum number of tokens to generate.
            max_steps: Optional maximum number of steps to execute.
            max_time: Optional maximum execution time in seconds.

        Returns:
            List[TaskResult]: List of TaskResult objects containing the generation results.

        Raises:
            ValueError: If variables is empty or invalid.
            RuntimeError: If task execution fails.
        """
        if not inputs:
            raise ValueError("Inputs cannot be empty")

        # Normalize models to list
        if models is None:
            models = [Model.GPT4O]
        elif isinstance(models, str):
            models = [models]

        # Set default workflow
        workflow = workflow or Simple

        # Normalize variables to dict
        if isinstance(inputs, str):
            inputs = {"prompt": inputs}

        # Apply configuration if set in class variables
        if max_tokens is not None:
            workflow.max_tokens = max_tokens
        if max_steps is not None:
            workflow.max_steps = max_steps
        if max_time is not None:
            workflow.max_time = max_time
            
        # Create tasks based on variables type
        try:
            if isinstance(inputs, list):
                tasks = [
                    Task(workflow=workflow(**i).build(), models=models)
                    for i in inputs
                ]
            else:
                tasks = [Task(workflow=workflow(**inputs).build(), models=models)]
        except Exception as e:
            raise ValueError(f"Failed to create tasks: {str(e)}")

        return await self.executor.execute(tasks)
