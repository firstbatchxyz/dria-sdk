from .base import DriaDataset
from typing import List, Dict, Optional, Union, Any, Type
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
from dria.factory.workflows.template import SingletonTemplate
from dria.client import Dria
from .utils import schemas_match, get_community_token
import json
import logging

logger = logging.getLogger(__name__)


class DatasetField:
    name: str
    prompt: Optional[str] = None
    workflow: Optional[Union[SingletonTemplate, List[SingletonTemplate]]] = None
    models: List[Model] = [Model.GPT4O_MINI]


class DatasetGenerator:
    def __init__(self, dataset: DriaDataset, dria_client: Optional[Dria] = None):
        self.dataset = dataset

        try:
            _id = self.dataset.db.get_dataset_id_by_name("rpc_url")
        except:
            token = get_community_token()
            _id = self.dataset.db.create_dataset(
                "rpc_url", "Stores the community rpc url"
            )
            self.dataset.db.add_entries(_id, [{"token": token}])
            logger.info(f"Created RPC token!")

        token = self.dataset.db.get_dataset_entries(_id, data_only=True)[0]["token"]
        self.dria_client = dria_client or Dria(rpc_token=token)

    def _validate_singletons(
        self,
        instructions: List[Dict[str, Any]],
        singletons: Union[Type[SingletonTemplate], List[Type[SingletonTemplate]]],
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
            current_schema = singletons[i].OutputSchema.model_json_schema()
            next_element = singletons[i + 1].model_json_schema()
            # check if matches
            if not schemas_match(current_schema, next_element):
                raise ValueError(
                    f"Schema mismatch. Outputs for {singletons[i].__name__} doesn't match inputs for {singletons[i + 1].__name__}."
                )

        if not schemas_match(
            singletons[-1].OutputSchema.model_json_schema(),
            self.dataset.schema.model_json_schema(),
        ):
            raise ValueError(
                f"Schema mismatch. Output of the last step: f{singletons[-1].__name__} doesn't match dataset schema."
            )

    async def _executor(
        self,
        instructions: List[Dict[str, Any]],
        singleton: Type[SingletonTemplate],
        models: List[Model],
    ):

        executor = ParallelSingletonExecutor(self.dria_client, singleton, self.dataset)
        executor.set_models(models)
        executor.load_instructions(instructions)
        return await executor.run()

    async def generate_dataset(
        self,
        instructions: List[Dict],
        singletons: Union[Type[SingletonTemplate], List[Type[SingletonTemplate]]],
        models: List[Model],
    ) -> None:
        """Generate data using Dria singleton.

        :param singletons:
        :param models:
        :param instructions:

        """
        if not isinstance(singletons, list):
            singletons = [singletons]

        try:
            self._validate_singletons(instructions, singletons)
        except ValueError as e:
            raise e

        step_map = []

        # Execute first step with instructions
        entry_ids, input_ids = await self._executor(instructions, singletons[0], models)
        step_map.append(
            [
                {"entry_id": entry_id, "input_id": input_id}
                for entry_id, input_id in zip(entry_ids, input_ids)
            ]
        )

        for singleton in singletons[1:]:
            name = self.dataset.name + "_" + singleton.__name__
            dataset_id = self.dataset.db.get_dataset_id_by_name(name)
            instructions = self.dataset.db.get_dataset_entries(
                dataset_id, data_only=True
            )
            entry_ids, input_ids = await self._executor(instructions, singleton, models)
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

    async def transform_and_update_dataset(
        self, field: DatasetField
    ) -> "DatasetGenerator":
        """
        Augments the dataset by adding a new field to the dataset.
        :param field: Dataset field
        """
        pass
