from dria import DriaDataset, Model, Dria
from dria.workflow.factory import GenerateGraph
import asyncio

my_dataset = DriaDataset(
    collection="graph_test",
)

dria = Dria()

inputs = [{"context": "The advantage of using AI on the healthcare"}]

asyncio.run(
    dria.generate(
        inputs=inputs, workflow=GenerateGraph, models=Model.GEMINI, dataset=my_dataset
    )
)

print(my_dataset.get_entries(data_only=True))
