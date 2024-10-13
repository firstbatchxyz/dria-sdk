from typing import List, Union, Tuple, Dict, Any
from dria.client import Dria
from dria.models import Task, Model
from dria.factory.workflows.template import SingletonTemplate

MAX_CONCURRENT: int = 1000


class ParallelSingletonExecutor:
    def __init__(
        self, dria_client: Dria, singleton: SingletonTemplate, batch_size: int = 100
    ):
        self.dria = dria_client
        self.singleton = singleton
        self.batch_size = batch_size
        self.instructions: List[Task] = []

    def load_instructions(self, inputs: List[Dict[str, Any]]):
        [self.instructions.append(self._create_task(inp)) for inp in inputs]

    async def execute_workflows(self):
        all_results = []
        for i in range(0, len(self.instructions), self.batch_size):
            batch = self.instructions[i : i + self.batch_size]
            # Execute tasks in batches, respecting the max_concurrent limit
            results = await self.dria.execute(batch)
            parsed_results = self._parse_results(results)
            all_results.extend(parsed_results)
        return all_results

    def _create_task(self, data: Dict[str, Any]) -> Task:
        workflow_data = self.singleton.workflow(**data).model_dump()
        return Task(workflow=workflow_data, models=[data.get("model", Model.OLLAMA)])

    def _parse_results(self, results: List[Any]) -> List[Any]:
        return self.singleton.parse_result(results)

    async def run(self):
        await self.dria.initialize()
        results = await self.execute_workflows()
        return results
