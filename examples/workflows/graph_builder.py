from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import GenerateGraph
import asyncio

my_dataset = DriaDataset(
    name="graph_test",
    description="test",
    schema=GenerateGraph.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [{"context": "The advantage of using AI on the healthcare"}]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=GenerateGraph,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
