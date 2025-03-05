import json
import logging
from typing import List, Dict, Any, Tuple, Type, Optional

from pydantic import BaseModel

from dria.executor import TaskExecutor
from dria.workflow.template import WorkflowTemplate
from dria.models import Task, Model, TaskResult
from dria.datasets.base import DriaDataset
from dria.constants import SCORING_BATCH_SIZE


class Batch:
    """
    Batch processing class for executing workflow tasks on datasets.

    This class handles batched execution of workflow templates against datasets,
    managing task creation, execution, result alignment, and storage.
    """

    def __init__(
        self,
        executor: TaskExecutor,
        workflow: Type[WorkflowTemplate],
        dataset: DriaDataset,
        batch_size: Optional[int] = None,
    ):
        """
        Initialize a Batch processor.

        Args:
            executor: TaskExecutor instance to run the tasks
            workflow: WorkflowTemplate class to process inputs
            dataset: DriaDataset containing the data to process
            batch_size: Optional size for processing batches, defaults to SCORING_BATCH_SIZE
        """
        self.executor = executor
        self.workflow = workflow
        self.dataset = dataset
        self.batch_size = batch_size or SCORING_BATCH_SIZE
        self.tasks: List[Task] = []
        self.models = [Model.OLLAMA]

        name = self.dataset.collection + "_" + self.workflow.__name__
        failed = self.dataset.collection + "_" + self.workflow.__name__ + "_failed"
        self.dataset_id = self.dataset.db.create_dataset(
            name, description=self.workflow.__name__
        )
        self.failed_dataset_id = self.dataset.db.create_dataset(
            failed, description=self.workflow.__name__
        )

    def load_instructions(self, inputs: List[Dict[str, Any]]):
        """
        Load input data and create corresponding tasks.

        Args:
            inputs: List of input dictionaries to process
        """
        for inp in inputs:
            task = self._create_task(inp)
            self.tasks.append(task)

    def set_models(self, models: List[Model]):
        """
        Set the models to use for task execution.

        Args:
            models: List of Model enums to use
        """
        self.models = models

    async def execute_workflows(self) -> Tuple[List[int], List[int]]:
        """
        Execute all loaded tasks in batches.

        Returns:
            Tuple containing (list of entry IDs, list of corresponding input indices)
        """
        entry_ids = []
        input_ids = []
        for i in range(0, len(self.tasks), self.batch_size):
            if self.executor.shutdown_event.is_set():
                break
            batch = self.tasks[i : i + self.batch_size]

            results, tasks = await self.executor.execute(batch)

            if tasks and isinstance(tasks, list) and isinstance(tasks[0], list):
                tasks = [task for batch in tasks for task in batch]

            try:
                ordered_entries, input_index = await self._align_results(results, tasks)
                entry_ids.extend(
                    self.dataset.db.add_entries(self.dataset_id, ordered_entries)
                )
                input_ids.extend(input_index)
            except Exception as e:
                logging.error(e)
                failed_data = [
                    {
                        "workflow": b.workflow,
                        "id": b.id,
                        "models": [model.value for model in b.models],
                    }
                    for b in batch
                ]
                self.dataset.db.add_entries(self.failed_dataset_id, failed_data)
        return entry_ids, input_ids

    def _create_task(self, data: Dict[str, Any]) -> Task:
        """
        Create a Task instance from input data.

        Args:
            data: Dictionary containing input data

        Returns:
            Task instance configured with workflow data
        """
        # Remove unnecessary fields from the input data
        workflow_data = self.workflow(**data).build()
        return Task(
            workflow=workflow_data,
            models=self.models,
            dataset_id=self.dataset.collection,
        )

    async def _align_results(
        self, results: List[TaskResult], tasks: List[Task]
    ) -> Tuple[List[Any], List[int]]:
        """
        Align results with original inputs and merge the data.

        Args:
            results: List of TaskResult objects from execution
            tasks: List of Task objects from execution

        Returns:
            Tuple containing (processed outputs, corresponding input indices)

        Raises:
            Exception: If result processing fails
        """
        # Handle empty results case
        if not results or not tasks:
            return [], []

        # Create mappings for task IDs to their original indices and results
        task_id_to_idx = {task.id: idx for idx, task in enumerate(tasks)}

        ordered_outputs = []
        corresponding_idx = []

        # Process each result by matching task IDs
        for result in results:
            if result.id in task_id_to_idx:
                idx = task_id_to_idx[result.id]

                # Process the result with contextualized callback
                try:
                    outputs = self.workflow().callback([result])

                    for output in outputs:
                        # Convert to JSON format
                        if isinstance(output, BaseModel):
                            parsed_output = output.model_dump_json(
                                indent=2, exclude_none=True, exclude_unset=True
                            )
                        else:
                            parsed_output = json.dumps(output, indent=2)
                        ordered_outputs.append(json.loads(parsed_output))
                        corresponding_idx.append(idx)
                except Exception as e:
                    logging.error(f"Callback error for task {result.id}: {e}")
                    continue

        return ordered_outputs, corresponding_idx

    async def run(self):
        """
        Execute all workflows and return results.

        Returns:
            Result of execute_workflows: (entry_ids, input_ids)
        """
        return await self.execute_workflows()
