import random

from .base import DriaDataset
from typing import List, Dict, Optional, Union, Any, Type
from dria.models import Model
from dria.batches import ParallelSingletonExecutor, ParallelPromptExecutor
from dria.factory.workflows.template import SingletonTemplate
from dria.client import Dria
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
            if self.dataset is None:
                token = get_community_token()
                self.dria_client = Dria(rpc_token=token, log_level=log_level)
            else:
                try:
                    _id = self.dataset.db.get_dataset_id_by_name("rpc_url")
                except Exception as e:
                    logging.debug(e)
                    token = get_community_token()
                    _id = self.dataset.db.create_dataset(
                        "rpc_url", "Stores the community rpc url"
                    )
                    self.dataset.db.add_entries(_id, [{"token": token}])
                    logger.info("Created RPC token!")

                token = self.dataset.db.get_dataset_entries(_id, data_only=True)[0][
                    "token"
                ]
                self.dria_client = Dria(rpc_token=token, log_level=log_level)
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

    def _validate_singletons(
        self,
        instructions: List[Dict[str, Any]],
        singletons: List[Type[SingletonTemplate]],
    ):
        """
        Validate singletons

        If a single singleton:
            Check input schema of singleton matches instructions
            Check output schema of singleton matches dataset schema
        If multiple singletons:
            Check input schema of first singletons matches instructions
            for i in range(len(singletons) - 1):
                current_schema = schema_func(data[i])
                next_element = data[i + 1]
                is_match = current_schema == schema_func(next_element)
                results.append((i, is_match))
            return results

        :param instructions:
        :param singletons:
        """

        def check_for_duplicates(lst):
            seen = set()
            for item in lst:
                if item in seen:
                    raise ValueError(
                        f"Duplicate found: {item}. Can't use same singleton twice."
                    )
                seen.add(item)

        # Name check
        check_for_duplicates([singleton.__name__ for singleton in singletons])

        for i, instruction in enumerate(instructions):
            if not schemas_match(instruction, singletons[0]):
                raise ValueError(
                    f"Schema mismatch between the first singleton {singletons[0].__name__} and {i}th instruction. \n{json.dumps(instruction, indent=2)}"
                )

        for i in range(len(singletons) - 1):
            current_schema = singletons[i].OutputSchema
            next_element = singletons[i + 1]
            # check if matches
            if not schemas_match(current_schema, next_element):
                raise ValueError(
                    f"Schema mismatch. Outputs for {singletons[i].__name__} doesn't match inputs for {singletons[i + 1].__name__}."
                )

        if not schemas_match(singletons[-1].OutputSchema, self.dataset.schema):
            raise ValueError(
                f"Schema mismatch. Output of the last step: {singletons[-1].__name__} doesn't match dataset schema."
            )

    async def _executor(
        self,
        instructions: List[Dict[str, Any]],
        singleton: Union[Type[SingletonTemplate], Prompt],
        models: List[Model],
    ):

        if isinstance(singleton, Prompt):
            executor = ParallelPromptExecutor(
                self.dria_client, singleton, self.dataset, self.batch_size
            )
            executor.set_models(models)
            executor.load_instructions(instructions)
            return await executor.run()
        else:
            executor = ParallelSingletonExecutor(
                self.dria_client, singleton, self.dataset, self.batch_size
            )
            executor.set_models(models)
            executor.load_instructions(instructions)
            return await executor.run()

    async def generate(
        self,
        instructions: Union[List[Dict[str, Any]], DriaDataset],
        singletons: Union[
            Type[SingletonTemplate], List[Type[SingletonTemplate]], Prompt
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

        if isinstance(singletons, Prompt):
            await self._with_prompt(instructions, singletons, models)
        else:
            await self._with_singletons(instructions, singletons, models)

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

    async def _with_singletons(
        self,
        instructions: List[Dict[str, Any]],
        singletons: Union[Type[SingletonTemplate], List[Type[SingletonTemplate]]],
        models: Union[Model, List[Model], List[List[Model]]],
    ) -> None:
        """Generate data using Dria singleton.

        :param singletons:
        :param models:
        :param instructions:

        """
        if not isinstance(singletons, list):
            singletons = [singletons]

        if not isinstance(models, list):
            models = [models]

        if isinstance(models[0], list):
            if len(models) != len(singletons):
                raise ValueError(
                    f"If you are providing a list of models for each singleton, "
                    f"it should have the same length. Number of models: {len(models)} number of singletons: {len(singletons)}"
                )
        else:
            models = [models] * len(singletons)

        try:
            self._validate_singletons(instructions, singletons)
        except ValueError as e:
            raise e

        step_map = []

        # Execute first step with instructions
        entry_ids, input_ids = await self._executor(
            instructions, singletons[0], models[0]
        )
        step_map.append(
            [
                {"entry_id": entry_id, "input_id": input_id}
                for entry_id, input_id in zip(entry_ids, input_ids)
            ]
        )

        for i in range(1, len(singletons)):
            name = self.dataset.name + "_" + singletons[i - 1].__name__
            dataset_id = self.dataset.db.get_dataset_id_by_name(name)
            instructions = self.dataset.db.get_dataset_entries(
                dataset_id, data_only=True
            )
            entry_ids, input_ids = await self._executor(
                instructions, singletons[i], models[i]
            )
            step_map.append(
                [
                    {"entry_id": entry_id, "input_id": input_id}
                    for entry_id, input_id in zip(entry_ids, input_ids)
                ]
            )

        # Assign last created as the main dataset
        name = self.dataset.name + "_" + singletons[-1].__name__
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
        :param prompt: Singleton or Prompt
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
