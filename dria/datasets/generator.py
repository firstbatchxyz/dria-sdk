import random

from .base import DriaDataset
from typing import List, Dict, Optional, Union, Any, Type
from dria.models import Model
from dria.batches import ParallelWorkflowExecutor, ParallelPromptExecutor
from dria.workflow.template import WorkflowTemplate
from dria import Dria
from hashlib import sha256
from .utils import schemas_match, get_community_token
import json
import logging
from .prompter import Prompt

logger = logging.getLogger(__name__)


class DatasetGenerator:
    def __init__(
        self,
        dataset: Optional[DriaDataset] = None,
        dria_client: Optional[Dria] = None,
        log_level=logging.INFO,
        batch_size: Optional[int] = None,
    ):
        self.batch_size = batch_size
        self.dataset = dataset
        if dria_client is None:
            self.dria_client = Dria(log_level=log_level)
        else:
            self.dria_client = dria_client

    def _validate_prompt(self, instructions: List[Dict[str, Any]], prompt: Prompt):

        for i, instruction in enumerate(instructions):
            if not set(prompt.variables).issubset(set(instruction.keys())):
                raise ValueError(
                    f"Schema mismatch between the prompt {prompt.prompt} and {i+1}. instruction. \n{json.dumps(instruction, indent=2)}"
                )
        if not schemas_match(
            prompt.schema,
            self.dataset.schema,
        ):
            raise ValueError(
                "Schema mismatch. Schema of the Prompt doesn't match dataset schema."
            )

    def set_dataset(self, dataset: DriaDataset) -> "DatasetGenerator":
        """Set the dataset for the generator.

        Args:
            dataset: DriaDataset to use for generation

        Returns:
            Self for chaining
        """
        self.dataset = dataset
        return self

    def set_batch_size(self, batch_size: int) -> "DatasetGenerator":
        self.batch_size = batch_size
        return self

    def _validate_workflows(
        self,
        instructions: List[Dict[str, Any]],
        workflows: List[Type[WorkflowTemplate]],
    ):
        """
        Validate workflows

        If a single workflow:
            Check input schema of workflow matches instructions
            Check output schema of workflow matches dataset schema
        If multiple workflows:
            Check input schema of first workflows matches instructions
            for i in range(len(workflows) - 1):
                current_schema = schema_func(data[i])
                next_element = data[i + 1]
                is_match = current_schema == schema_func(next_element)
                results.append((i, is_match))
            return results

        :param instructions:
        :param workflows:
        """

        def check_for_duplicates(lst):
            seen = set()
            for item in lst:
                if item in seen:
                    raise ValueError(
                        f"Duplicate found: {item}. Can't use same workflow twice."
                    )
                seen.add(item)

        # Name check
        check_for_duplicates([workflow.__name__ for workflow in workflows])

        for i, instruction in enumerate(instructions):
            if not schemas_match(instruction, workflows[0]):
                raise ValueError(
                    f"Schema mismatch between the first workflow {workflows[0].__name__} and {i}th instruction. \n{json.dumps(instruction, indent=2)}"
                )

        for i in range(len(workflows) - 1):
            current_schema = workflows[i].OutputSchema
            next_element = workflows[i + 1]
            # check if matches
            if not schemas_match(current_schema, next_element):
                raise ValueError(
                    f"Schema mismatch. Outputs for {workflows[i].__name__} doesn't match inputs for {workflows[i + 1].__name__}."
                )

        if not schemas_match(workflows[-1].OutputSchema, self.dataset.schema):
            raise ValueError(
                f"Schema mismatch. Output of the last step: {workflows[-1].__name__} doesn't match dataset schema."
            )

    async def _executor(
        self,
        instructions: List[Dict[str, Any]],
        workflow: Union[Type[WorkflowTemplate], Prompt],
        models: List[Model],
    ):

        if isinstance(workflow, Prompt):
            executor = ParallelPromptExecutor(
                self.dria_client, workflow, self.dataset, self.batch_size
            )
            executor.set_models(models)
            executor.load_instructions(instructions)
            return await executor.run()
        else:
            executor = ParallelWorkflowExecutor(
                self.dria_client, workflow, self.dataset, self.batch_size
            )
            executor.set_models(models)
            executor.load_instructions(instructions)
            return await executor.run()

    async def generate(
        self,
        instructions: Union[List[Dict[str, Any]], DriaDataset],
        workflows: Union[
            Type[WorkflowTemplate], List[Type[WorkflowTemplate]], Prompt
        ],
        models: Optional[Union[Model, List[Model], List[List[Model]]]] = None,
        sampling_ratio: float = 1.0,
    ) -> None:

        if self.dataset is None:
            raise ValueError(
                "Dataset must be defined before calling generate(). Use set_dataset() to define a dataset."
            )

        if models is None:
            models = [
                Model.GPT4O,
                Model.GPT4O_MINI,
                Model.GEMINI_15_FLASH,
                Model.GEMINI_20_FLASH,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
            ]

        if sampling_ratio < 1.0:
            num_samples = int(len(instructions) * sampling_ratio)
            if num_samples == 0:
                num_samples = 1
            instructions = random.sample(instructions, num_samples)

        # TODO: Handle streaming for large instructions
        if isinstance(instructions, DriaDataset):
            instructions = instructions.get_entries(data_only=True)

        if isinstance(workflows, Prompt):
            await self._with_prompt(instructions, workflows, models)
        else:
            await self._with_workflows(instructions, workflows, models)

    async def _with_prompt(
        self,
        instructions: List[Dict[str, Any]],
        prompt: Prompt,
        models: Union[Model, List[Model]],
    ):

        try:
            self._validate_prompt(instructions, prompt)
        except ValueError as e:
            raise e

        if not isinstance(models, list):
            models = [models]

        _, _ = await self._executor(instructions, prompt, models)

        name = (
            self.dataset.name + "_" + sha256(prompt.prompt.encode("utf-8")).hexdigest()
        )
        dataset_id = self.dataset.db.get_dataset_id_by_name(name)
        final_entries = self.dataset.db.get_dataset_entries(dataset_id, data_only=True)

        final_db = self.dataset.db.get_dataset_id_by_name(self.dataset.name)
        self.dataset.db.add_entries(final_db, final_entries)

    async def _with_workflows(
        self,
        instructions: List[Dict[str, Any]],
        workflows: Union[Type[WorkflowTemplate], List[Type[WorkflowTemplate]]],
        models: Union[Model, List[Model], List[List[Model]]],
    ) -> None:
        """Generate data using Dria workflow.

        :param workflows:
        :param models:
        :param instructions:

        """
        if not isinstance(workflows, list):
            workflows = [workflows]

        if not isinstance(models, list):
            models = [models]

        if isinstance(models[0], list):
            if len(models) != len(workflows):
                raise ValueError(
                    f"If you are providing a list of models for each workflow, "
                    f"it should have the same length. Number of models: {len(models)} number of workflows: {len(workflows)}"
                )
        else:
            models = [models] * len(workflows)

        try:
            self._validate_workflows(instructions, workflows)
        except ValueError as e:
            raise e

        step_map = []

        # Execute first step with instructions
        entry_ids, input_ids = await self._executor(
            instructions, workflows[0], models[0]
        )
        step_map.append(
            [
                {"entry_id": entry_id, "input_id": input_id}
                for entry_id, input_id in zip(entry_ids, input_ids)
            ]
        )

        for i in range(1, len(workflows)):
            name = self.dataset.name + "_" + workflows[i - 1].__name__
            dataset_id = self.dataset.db.get_dataset_id_by_name(name)
            instructions = self.dataset.db.get_dataset_entries(
                dataset_id, data_only=True
            )
            entry_ids, input_ids = await self._executor(
                instructions, workflows[i], models[i]
            )
            step_map.append(
                [
                    {"entry_id": entry_id, "input_id": input_id}
                    for entry_id, input_id in zip(entry_ids, input_ids)
                ]
            )

        # Assign last created as the main dataset
        name = self.dataset.name + "_" + workflows[-1].__name__
        dataset_id = self.dataset.db.get_dataset_id_by_name(name)
        final_entries = self.dataset.db.get_dataset_entries(dataset_id, data_only=True)

        final_db = self.dataset.db.get_dataset_id_by_name(self.dataset.name)
        self.dataset.db.add_entries(final_db, final_entries)

        # TODO: decide what to do with step_map, write on db, or store locally, or none

    async def enrich(
        self,
        prompt: Prompt,
        models: Union[Model, List[Model]],
    ) -> "DatasetGenerator":
        """
        Augments the dataset by adding a new field to the dataset or updating an existing field.
        :param prompt: Workflow or Prompt
        :param models: Model or List of Models
        """
        if self.dataset is None:
            raise ValueError(
                "Dataset must be defined before calling enrich(). Use set_dataset() to define a dataset."
            )

        instructions = self.dataset.get_entries(data_only=True)
        try:
            self._validate_prompt(instructions, prompt)
        except ValueError as e:
            raise e

        if not isinstance(models, list):
            models = [models]

        _, _ = await self._executor(instructions, prompt, models)

        name = (
            self.dataset.name + "_" + sha256(prompt.prompt.encode("utf-8")).hexdigest()
        )
        dataset_id = self.dataset.db.get_dataset_id_by_name(name)
        final_entries = self.dataset.db.get_dataset_entries(dataset_id, data_only=True)
        transformed_dict = {
            key: [d[key] for d in final_entries] for key in final_entries[0].keys()
        }
        _id = self.dataset.dataset_id
        self.dataset.db.add_fields_to_entries(_id, transformed_dict)
        return self
