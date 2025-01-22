import json
import logging
from typing import List, Dict, Any, Tuple, Type, Optional
from dria.constants import TASK_TIMEOUT
from dria.client import Dria
from dria.factory.workflows.template import SingletonTemplate
from dria.models import Task, Model, TaskResult
from dria.datasets.base import DriaDataset
from dria.constants import SCORING_BATCH_SIZE


class ParallelSingletonExecutor:
    def __init__(
        self,
        dria_client: Dria,
        singleton: Type[SingletonTemplate],
        dataset: DriaDataset,
        batch_size: Optional[int] = None,
    ):
        self.dria = dria_client
        self.singleton = singleton
        self.dataset = dataset
        self.batch_size = batch_size or SCORING_BATCH_SIZE
        self.instructions: Tuple[List[Task], List[Dict[str, Any]]] = ([], [])
        self.models = [Model.OLLAMA]

        name = self.dataset.name + "_" + self.singleton.__name__
        failed = self.dataset.name + "_" + self.singleton.__name__ + "_failed"
        self.dataset_id = self.dataset.db.create_dataset(
            name, description=self.singleton.__name__
        )
        self.failed_dataset_id = self.dataset.db.create_dataset(
            failed, description=self.singleton.__name__
        )

    def load_instructions(self, inputs: List[Dict[str, Any]]):
        for inp in inputs:
            self.instructions[0].append(self._create_task(inp))
            self.instructions[1].append(inp)

    def set_models(self, models: List[Model]):
        self.models = models

    async def execute_workflows(self) -> Tuple[List[int], List[int]]:
        entry_ids = []
        input_ids = []
        for i in range(0, len(self.instructions[0]), self.batch_size):
            if self.dria.shutdown_event.is_set():
                break
            batch = self.instructions[0][i : i + self.batch_size]
            original_inputs = self.instructions[1][i : i + self.batch_size]

            results = await self.dria.execute(batch, timeout=len(batch) * TASK_TIMEOUT)
            try:
                ordered_entries, input_index = self._align_results(
                    results, original_inputs
                )
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
        # Remove unnecessary fields from the input data
        data = {k: data[k] for k in self.singleton.model_fields.keys() if k != "params"}
        workflow_data = self.singleton.create(**data).workflow()
        return Task(
            workflow=workflow_data, models=self.models, dataset_id=self.dataset.name
        )

    def _align_results(
        self, results: List[TaskResult], original_inputs: List[Dict]
    ) -> Tuple[List[Any], List[int]]:
        """
        Align results with original inputs and merge the data.
        Handles dynamic singleton initialization for each input context.
        """
        task_inputs = [r.task_input for r in results]
        common_keys = set(task_inputs[0].keys()) & set(original_inputs[0].keys())

        def create_lookup_key(input_dict: Dict) -> str:
            normalized = {}
            for k in sorted(common_keys):
                val = input_dict[k]
                # If val is a JSON string, parse it first
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except json.JSONDecodeError:
                        pass
                normalized[k] = val
            return json.dumps(normalized, sort_keys=True)

        # Create lookup for raw results with normalized keys
        result_lookup = {}
        for result, task_input in zip(results, task_inputs):
            key = create_lookup_key(task_input)
            result_lookup[key] = (result, task_input)

        ordered_outputs = []
        corresponding_idx = []
        for idx, original_input in enumerate(original_inputs):
            lookup_key = create_lookup_key(original_input)
            if lookup_key in result_lookup:
                result, task_input = result_lookup[lookup_key]

                # Initialize singleton with original input context
                data = {
                    k: original_input[k]
                    for k in self.singleton.model_fields.keys()
                    if k != "params"
                }
                singleton_instance = self.singleton.create(**data)

                # Process the result with contextualized callback
                try:
                    outputs = singleton_instance.callback([result])
                except Exception as e:
                    logging.error(e)
                    continue

                for output in outputs:
                    # Convert to JSON format
                    parsed_output = output.model_dump_json(
                        indent=2, exclude_none=True, exclude_unset=True
                    )
                    ordered_outputs.append(json.loads(parsed_output))
                    corresponding_idx.append(idx)
            else:
                logging.debug(
                    f"Warning: No match found for input: {original_input}\nCurrent Lookup Keys: {result_lookup}"
                )

        return ordered_outputs, corresponding_idx

    async def run(self):
        return await self.execute_workflows()
