from typing import List, Union, Tuple, Dict, Any
from datasets import load_dataset
from dria.client import Dria
from dria.models import Task
from dria.factory.workflows.template import SingletonTemplate

MAX_CONCURRENT: int = 1000


class ParallelWorkflowExecutor:
    def __init__(
        self, dria_client: Dria, workflow: SingletonTemplate, batch_size: int = 100
    ):
        self.dria = dria_client
        self.workflow = workflow
        self.batch_size = batch_size

    @staticmethod
    async def load_instructions(
        dataset_name: str, split: str = "train"
    ) -> List[Tuple[str, Dict[str, Any]]]:
        dataset = load_dataset(dataset_name, split=split)
        return [(row["instruction"], row) for row in dataset]

    async def execute_workflows(
        self,
        inputs: List[Tuple[str, Dict[str, Any]]],
    ):
        all_results = []
        for i in range(0, len(inputs), self.batch_size):
            batch = inputs[i : i + self.batch_size]
            tasks = [
                self._create_task(instruction, data) for instruction, data in batch
            ]

            # Execute tasks in batches, respecting the max_concurrent limit
            for j in range(0, len(tasks), MAX_CONCURRENT):
                sub_batch = tasks[j : j + MAX_CONCURRENT]
                results = await self.dria.execute(sub_batch)
                parsed_results = self._parse_results(results)
                all_results.extend(parsed_results)

        return all_results

    def _create_task(self, instruction: str, data: Dict[str, Any]) -> Task:
        workflow_data = self.workflow.workflow(
            instruction=instruction, **data
        ).model_dump()
        return Task(workflow=workflow_data, models=[data.get("model", "default_model")])

    def _parse_results(self, results: List[Any]) -> List[Any]:
        return [self.workflow.parse_result(result) for result in results]

    async def run(self, dataset_name: str, split: str = "train"):
        await self.dria.initialize()
        instructions = await self.load_instructions(dataset_name, split)
        results = await self.execute_workflows(instructions)
        return results
