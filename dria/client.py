import asyncio
import logging
import os
from typing import Dict, List, Type, Optional, Union, Any

from dria.constants import PROVIDERS, MONITORING_INTERVAL
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.datasets.base import DriaDataset
from dria.executor import TaskExecutor, Ping, Batch
from dria.executor.utils import get_community_token
from dria.manager import TaskManager
from dria.models import Model, TaskResult, Task
from dria.request import RPCClient
from dria.workflow import WorkflowTemplate
from dria.workflow.factory import Simple

from rich.console import Console
from rich.table import Table


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

        self._initialize_auth()
        self._initialize_components()
        self._initialized = True

    def _initialize_auth(self) -> None:
        """Initialize authentication token."""
        rpc_token = get_community_token() or os.environ.get("DRIA_RPC_TOKEN")
        if not rpc_token:
            raise ValueError(
                "No RPC token provided. Set DRIA_RPC_TOKEN or pass rpc_token"
            )
        self.rpc = RPCClient(auth_token=rpc_token)

    def _initialize_components(self) -> None:
        """Initialize core system components."""
        self.storage = Storage()
        self.kv = KeyValueQueue()

        ping = Ping(self.storage, self.rpc, self.kv)
        task_manager = TaskManager(self.storage, self.rpc, self.kv)

        self.executor = TaskExecutor(
            ping=ping,
            rpc=self.rpc,
            storage=self.storage,
            kv=self.kv,
            task_manager=task_manager,
        )

    @staticmethod
    def _apply_workflow_config(
        workflow: Union[Type[WorkflowTemplate], List[Type[WorkflowTemplate]]],
        max_tokens: Optional[int] = None,
        max_steps: Optional[int] = None,
        max_time: Optional[int] = None,
    ) -> None:
        """
        Apply configuration parameters to workflow template(s).

        This method demonstrates how the Factory Pattern allows for configuration
        of workflow templates before instantiation. By setting class variables on
        the workflow template classes, all instances created from those classes
        will inherit the configuration.

        This is a key benefit of the Factory Pattern - the ability to configure
        the factory (workflow template class) before creating products (workflow instances).

        Args:
            workflow: Workflow template class(es) to configure
            max_tokens: Maximum number of tokens for the workflow
            max_steps: Maximum number of steps for the workflow
            max_time: Maximum execution time in seconds
        """
        workflows = [workflow] if not isinstance(workflow, list) else workflow

        for w in workflows:
            if max_tokens is not None:
                w.max_tokens = max_tokens
            if max_steps is not None:
                w.max_steps = max_steps
            if max_time is not None:
                w.max_time = max_time

    @staticmethod
    def _normalize_inputs(
        inputs: Union[List[Dict[str, Any]], Dict[str, Any], str, List[str]]
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Normalize input data to dictionary format.

        Args:
            inputs: Input data in various formats

        Returns:
            Normalized input data as dictionary or list of dictionaries
        """
        if isinstance(inputs, str):
            return {"prompt": inputs}
        elif isinstance(inputs, list) and all(isinstance(i, str) for i in inputs):
            return [{"prompt": i} for i in inputs]
        return inputs

    @staticmethod
    def _normalize_models(
        models: Optional[Union[Model, List[Model], List[List[Model]]]]
    ) -> List[Model]:
        """
        Normalize models to list format.

        Args:
            models: Model(s) in various formats

        Returns:
            Normalized list of models
        """
        if models is None:
            return [Model.GPT4O]
        if isinstance(models, (str, Model)):
            return [models]
        return models

    async def generate(
        self,
        inputs: Union[List[Dict[str, Any]], Dict[str, Any], List[str], str],
        workflow: Optional[
            Union[Type[WorkflowTemplate], List[Type[WorkflowTemplate]]]
        ] = None,
        models: Optional[Union[Model, List[Model], List[List[Model]]]] = None,
        dataset: Optional["DriaDataset"] = None,
        batch_size: Optional[int] = 50,
        max_tokens: Optional[int] = None,
        max_steps: Optional[int] = None,
        max_time: Optional[int] = None,
            generate_all_models: bool = False
    ) -> Union[List[TaskResult], None]:
        """
        Generate tasks from inputs and execute workflows.

        Args:
            inputs: Input data that can be:
                   - List of instruction dictionaries
                   - Single dictionary
                   - Prompt string
                   - List of prompt strings
            workflow: Optional workflow template class that builds the task workflow.
                     Defaults to Simple workflow if not provided.
            models: Optional model(s) to use for task execution.
                   Can be a single model, list of models, or list of model lists.
                   Defaults to GPT-4O if not provided.
            dataset: Optional DriaDataset instance to store results.
            batch_size: Optional batch size for parallel execution.
            max_tokens: Optional maximum number of tokens to generate.
            max_steps: Optional maximum number of steps to execute.
            max_time: Optional maximum execution time in seconds.
            generate_all_models: Boolean for generating all tasks to chosen models

        Returns:
            List[TaskResult] for direct generation, None for dataset generation

        Raises:
            ValueError: If inputs is empty or invalid.
            RuntimeError: If task execution fails.
        """
        if not inputs:
            raise ValueError("Inputs cannot be empty")

        workflow = workflow or Simple
        models = self._normalize_models(models)
        inputs = self._normalize_inputs(inputs)

        if not isinstance(inputs, List):
            inputs = [inputs]

        self._apply_workflow_config(workflow, max_tokens, max_steps, max_time)

        # If multiple workflows, dataset is required
        if isinstance(workflow, list) and not dataset:
            raise ValueError(
                "Dataset is required when using multiple workflows. For example: "
                "dria.generate(inputs=data, workflow=[Workflow1, Workflow2], dataset=DriaDataset('my_dataset'))"
            )

        if dataset:
            if workflow is None:
                raise ValueError("Workflow must be provided for dataset generation")

            await self._with_workflows(
                dataset=dataset,
                inputs=inputs,
                workflows=workflow,
                models=models,
                batch_size=batch_size,
                generate_all_models=generate_all_models
            )
            return None

        try:
            tasks = self._create_tasks(inputs, workflow, models, generate_all_models)
            results, tasks = await self.executor.execute(tasks)
            return workflow().callback(results)
        except Exception as e:
            raise ValueError(f"Failed to create tasks: {str(e)}")

    async def check_model_availability(
        self, models: Optional[Union[Model, List[Model]]] = None
    ) -> None:
        """
        Check if models are available on the network.

        Args:
            models: A single model or list of models to check availability for.
                   If None, checks availability for all models.

        Returns:
            None: Prints a table of available models and node counts
        """
        all_model_nodes = {}
        await self.executor.ping.run()

        if models is None:
            # Check all models if none specified
            models = list(Model)

        if not isinstance(models, list):
            models = [models]

        for model in models:
            nodes = await self.executor.task_manager.get_available_nodes(model.value)
            if nodes:
                all_model_nodes[model] = len(nodes)

        if not all_model_nodes:
            await asyncio.sleep(MONITORING_INTERVAL)
            await self.executor.ping.run()

        # Sort model nodes by count (high to low)
        sorted_models = sorted(
            all_model_nodes.items(), key=lambda item: item[1], reverse=True
        )

        console = Console()
        table = Table(title="Model Availability")

        table.add_column("Model", style="cyan")
        table.add_column("Available Nodes", style="green")

        for model, count in sorted_models:
            table.add_row(
                (
                    model.name
                    if model.name not in PROVIDERS
                    else model.name + " [all models on the provider]"
                ),
                str(count),
            )

        console.print(table)

    @staticmethod
    def _create_tasks(
        inputs: List[Dict[str, Any]],
        workflow: Type[WorkflowTemplate],
        models: List[Model],
        generate_all_models: bool = False
    ) -> List[Task]:
        """
        Create task instances from inputs.

        Args:
            inputs: List of input dictionaries
            workflow: Workflow template class
            models: List of models to use
            generate_all_models: Boolean for generating all tasks to chosen models

        Returns:
            List of Task objects
        """
        tasks = []
        if generate_all_models:
            for model in models:
                tasks.extend([Task(workflow=workflow(**i).build(), models=[model]) for i in inputs])
        else:
            tasks = [Task(workflow=workflow(**i).build(), models=models) for i in inputs]
        return tasks

    async def _with_workflows(
        self,
        dataset: "DriaDataset",
        inputs: List[Dict[str, Any]],
        workflows: Union[Type[WorkflowTemplate], List[Type[WorkflowTemplate]]],
        models: Union[Model, List[Model], List[List[Model]]],
        batch_size: Optional[int] = 50,
        generate_all_models: bool = False
    ) -> None:
        """
        Generate data using Dria workflow.

        Args:
            dataset: Target dataset to store results
            inputs: List of inputs to process
            workflows: Single workflow or list of workflows to execute
            models: Model(s) to use for generation
            batch_size: Optional batch size for parallel execution.
            generate_all_models: Boolean for generating all tasks to chosen models

        Raises:
            ValueError: If model and workflow configurations are incompatible
        """
        if isinstance(workflows, list) and generate_all_models:
            raise ValueError(
                f"generate_all_models parameter is not supported on multiple workflow."
                f" Use for loop on models instead."
            )
        workflows = [workflows] if not isinstance(workflows, list) else workflows
        models = [models] if not isinstance(models, list) else models

        if isinstance(models[0], list):
            if len(models) != len(workflows):
                raise ValueError(
                    f"If providing a list of models for each workflow, "
                    f"lengths must match. Models: {len(models)}, workflows: {len(workflows)}"
                )
        else:
            models = [models] * len(workflows)

        self._validate_workflows(workflows)
        _ = await self._execute_workflow_chain(
            dataset, inputs, workflows, models, batch_size, generate_all_models
        )

        # Finalize dataset
        self._finalize_dataset(dataset, workflows)

    async def _execute_workflow_chain(
        self,
        dataset: "DriaDataset",
        initial_inputs: List[Dict[str, Any]],
        workflows: List[Type[WorkflowTemplate]],
        models: List[List[Model]],
        batch_size: int,
        generate_all_models: bool = False
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute chain of workflows sequentially.

        Args:
            dataset: Target dataset to store results
            initial_inputs: Initial inputs for the first workflow
            workflows: List of workflow templates to execute
            models: List of model lists for each workflow
            batch_size: Batch size for parallel execution
            generate_all_models: Boolean for generating all tasks to chosen models

        Returns:
            List of step mappings between entry IDs and input IDs
        """
        step_map = []
        current_inputs = initial_inputs

        for i, (workflow, model_set) in enumerate(zip(workflows, models)):
            executor = Batch(self.executor, workflow, dataset, batch_size)
            executor.set_models(model_set)
            executor.load_instructions(current_inputs, generate_all_models)

            entry_ids, input_ids = await executor.run()
            step_map.append(
                [
                    {"entry_id": entry_id, "input_id": input_id}
                    for entry_id, input_id in zip(entry_ids, input_ids)
                ]
            )

            if i < len(workflows) - 1:
                name = f"{dataset.collection}_{workflow.__name__}"
                dataset_id = dataset.db.get_dataset_id_by_name(name)
                current_inputs = dataset.db.get_dataset_entries(
                    dataset_id, data_only=True
                )

        return step_map

    @staticmethod
    def _finalize_dataset(
        dataset: "DriaDataset", workflows: List[Type[WorkflowTemplate]]
    ) -> None:
        """
        Finalize dataset by copying final results to main collection.

        Args:
            dataset: Target dataset to finalize
            workflows: List of workflow templates that were executed
        """
        name = f"{dataset.collection}_{workflows[-1].__name__}"
        dataset_id = dataset.db.get_dataset_id_by_name(name)
        final_entries = dataset.db.get_dataset_entries(dataset_id, data_only=True)

        final_db = dataset.db.get_dataset_id_by_name(dataset.collection)
        dataset.db.add_entries(final_db, final_entries)

    @staticmethod
    def _validate_workflows(
        workflows: List[Type[WorkflowTemplate]],
    ) -> None:
        """
        Validate workflow chain compatibility.

        Args:
            workflows: List of workflow templates to validate

        Raises:
            ValueError: If validation fails
        """

        def check_for_duplicates(lst):
            seen = set()
            for item in lst:
                if item in seen:
                    raise ValueError(
                        f"Duplicate found: {item}. Can't use same workflow twice."
                    )
                seen.add(item)

        # Validate workflow names
        check_for_duplicates([workflow.__name__ for workflow in workflows])
