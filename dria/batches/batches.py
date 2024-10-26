from typing import List, Dict, Any

from dria.client import Dria
from dria.factory.workflows.template import SingletonTemplate
from dria.models import Task, Model
from dria.utils.logging import logger

MAX_CONCURRENT: int = 1000


class ParallelSingletonExecutor:
    def __init__(
            self, dria_client: Dria, singleton: SingletonTemplate, batch_size: int = 100
    ):
        self.dria = dria_client
        self.singleton = singleton
        self.batch_size = batch_size
        self.instructions: List[Task] = []
        self.models = [Model.OLLAMA]
        self.timeout = 60

    def load_instructions(self, inputs: List[Dict[str, Any]]):
        for inp in inputs:
            self.instructions.append(self._create_task(inp))
        ratio = len(self.instructions) / 10
        if ratio > self.timeout:
            if ratio > 30:
                new_timeout = int(ratio)
                logger.warning(
                    f"Instruction size is too large for setting timeout {self.timeout}."
                    f" Setting timeout to {new_timeout} seconds."
                )
                self.timeout = new_timeout
            else:
                logger.warning(
                    f"Instruction size is too large for setting timeout {self.timeout}."
                    f"Setting timeout to 30 seconds."
                )
                self.timeout = 30

    def set_models(self, models: List[Model]):
        self.models = models

    def set_timeout(self, timeout: int):
        self.timeout = timeout

    async def execute_workflows(self):
        all_results = []
        for i in range(0, len(self.instructions), self.batch_size):
            batch = self.instructions[i: i + self.batch_size]
            # Execute tasks in batches, respecting the max_concurrent limit
            results = await self.dria.execute(batch, timeout=self.timeout)
            parsed_results = self._parse_results(results)
            all_results.extend(parsed_results)
        return all_results

    def _create_task(self, data: Dict[str, Any]) -> Task:
        workflow_data = self.singleton.workflow(**data).model_dump()
        return Task(workflow=workflow_data, models=self.models)

    def _parse_results(self, results: List[Any]) -> List[Any]:
        return self.singleton.parse_result(results)

    async def run(self):
        results = await self.execute_workflows()
        return results
