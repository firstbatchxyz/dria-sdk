from .base import DriaDataset
from typing import List, Dict, Optional, Union, Any
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
from dria.factory.workflows.template import SingletonTemplate
from dria.client import Dria
from .utils import schemas_match
import json


class DatasetField:
    name: str
    prompt: Optional[str] = None
    workflow: Optional[Union[SingletonTemplate, List[SingletonTemplate]]] = None
    models: List[Model] = [Model.GPT4O_MINI]


class DatasetGenerator:
    def __init__(self, dataset: DriaDataset, dria_client: Optional[Dria] = None):
        self.dataset = dataset
        self.dria_client = dria_client or Dria()

    def _validate_singletons(
        self,
        instructions: List[Dict[str, Any]],
        singletons: Union[SingletonTemplate, List[SingletonTemplate]],
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
        for i, instruction in enumerate(instructions):
            if not schemas_match(instruction, singletons[0]):
                raise ValueError(
                    f"Schema mismatch between the first singleton {singletons[0].__class__.__name__} and {i}th instruction. \n{json.dumps(instruction, indent=2)}"
                )

        for i in range(len(singletons) - 1):
            current_schema = singletons[i].OutputSchema.model_json_schema()
            next_element = singletons[i + 1].model_json_schema()
            # check if matches
            if not schemas_match(current_schema, next_element):
                raise ValueError(
                    f"Schema mismatch. Outputs for {singletons[i].__class__.__name__} doesn't match inputs for {singletons[i + 1].__class__.__name__}."
                )

        if not schemas_match(
            singletons[-1].OutputSchema.model_json_schema(),
            self.dataset.schema.model_json_schema(),
        ):
            raise ValueError(
                f"Schema mismatch. Output of the last step: f{singletons[-1].__class__.__name__} doesn't match dataset schema."
            )

    async def _executor(
        self,
        instructions: List[Dict[str, Any]],
        singleton: SingletonTemplate,
        models: List[Model],
    ):

        executor = ParallelSingletonExecutor(self.dria_client, singleton, self.dataset)
        executor.set_models(models)
        executor.load_instructions(instructions)
        return await executor.run()

    async def generate_dataset(
        self,
        singletons: Union[SingletonTemplate, List[SingletonTemplate]],
        models: List[Model],
        instructions: List[Dict],
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

        step_map = {singleton.__class__.__name__: [] for singleton in singletons}

        # Execute first step with instructions
        entry_ids = await self._executor(instructions, singletons[0], models)
        step_map[singletons[0].__class__.__name__].append(entry_ids)

        for singleton in singletons[1:]:
            name = self.dataset.name + "_" + singleton.__class__.__name__
            dataset_id = self.dataset.db.create_dataset(
                name, description=singleton.__class__.__name__
            )
            instructions = self.dataset.db.get_dataset_entries(
                dataset_id, data_only=True
            )
            entry_ids = await self._executor(instructions, singleton, models)
            step_map[singletons[0].__class__.__name__].append(entry_ids)

        # Assign last created as the main dataset
        name = self.dataset.name + "_" + singletons[-1].__class__.__name__
        dataset_id = self.dataset.db.create_dataset(
            name, description=singletons[-1].__class__.__name__
        )
        final_entries = self.dataset.db.get_dataset_entries(dataset_id, data_only=True)

        final_db = self.dataset.db.create_dataset(
            self.dataset.name, self.dataset.description
        )
        self.dataset.db.add_entries(final_db, final_entries)

    async def transform_and_update_dataset(
        self, field: DatasetField
    ) -> "DatasetGenerator":
        """
        Augments the dataset by adding a new field to the dataset.
        :param field: Dataset field
        """
        pass
