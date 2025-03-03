import json
from dria import DriaDataset, Model, Dria
from dria.workflow.factory import GenerateSubtopics
import asyncio


dria = Dria()
my_dataset = DriaDataset(collection="subtopics")

asyncio.run(
    dria.generate(
        inputs={"topic": "Artificial Intelligence"},
        workflow=GenerateSubtopics,
        models=Model.GPT4O,
        dataset=my_dataset,
    )
)
entries = my_dataset.get_entries(True)

print(json.dumps(entries, indent=2))
