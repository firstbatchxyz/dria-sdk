import json
import logging
import traceback
from typing import List, Dict, Any, Tuple, Optional
from dria.constants import TASK_TIMEOUT
from dria.client import Dria
from dria.datasets.prompter import Prompt
from dria.models import Task, Model, TaskResult
from dria.datasets.base import DriaDataset
from dria.constants import SCORING_BATCH_SIZE
from hashlib import sha256


class ParallelPromptExecutor:
    def __init__(
        self,
        dria_client: Dria,
        prompt: Prompt,
        dataset: DriaDataset,
        batch_size: Optional[int] = None,
    ):
        self.dria = dria_client
        self.prompt = prompt
        self.dataset = dataset
        self.batch_size = batch_size or SCORING_BATCH_SIZE
        self.instructions: Tuple[List[Task], List[Dict[str, Any]]] = ([], [])
        self.models = [Model.GPT4O_MINI]

        self.hash = sha256(self.prompt.prompt.encode("utf-8")).hexdigest()
        name = self.dataset.name + "_" + self.hash

        failed = self.dataset.name + "_" + self.hash + "_failed"
        self.dataset_id = self.dataset.db.create_dataset(
            name, description=self.prompt.description
        )
        self.failed_dataset_id = self.dataset.db.create_dataset(
            failed, description=self.prompt.description
        )

    def load_instructions(self, inputs: List[Dict[str, Any]]):
        for inp in inputs:
            self.instructions[0].append(self._create_task(inp))
            self.instructions[1].append(inp)

    def set_models(self, models: List[Model]):
        # Only allow models with Structured outputs
        allowed_models = [
            Model.GPT4O_MINI,
            Model.GPT4O,
            Model.GEMINI_15_FLASH,
            Model.GEMINI_20_FLASH,
            Model.GEMINI_15_PRO,
            Model.QWEN2_5_32B_FP16,
        ]
        intersect = set(allowed_models).intersection(set(models))
        if len(intersect) == 0:
            raise ValueError(
                f"Selected models must be on of structured output supporting models {allowed_models}"
            )

        self.models = list(intersect)

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
                logging.debug(e)
                failed_data = [
                    {
                        "workflow": b.workflow.model_dump(
                            exclude={"tasks": {"__all__": {"schema"}}}
                        ),
                        "id": b.id,
                        "models": [model.value for model in b.models],
                        "traceback": str(traceback.format_exc()),
                    }
                    for b in batch
                ]
                self.dataset.db.add_entries(self.failed_dataset_id, failed_data)
        return entry_ids, input_ids

    def _create_task(self, data: Dict[str, Any]) -> Task:
        workflow_data = self.prompt.workflow(**data)
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

                # Process the result with contextualized callback
                outputs = self.prompt.callback([result])

                for output in outputs:
                    # Convert to JSON format
                    parsed_output = output.model_dump_json(
                        indent=2, exclude_none=True, exclude_unset=True
                    )
                    ordered_outputs.append(json.loads(parsed_output))
                    corresponding_idx.append(idx)
            else:
                logging.debug(f"Warning: No match found for input: {original_input}")

        return ordered_outputs, corresponding_idx

    async def run(self):
        return await self.execute_workflows()
