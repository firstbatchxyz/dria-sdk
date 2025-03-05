import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import PersonaBio

dria = Dria()
my_dataset = DriaDataset(collection="pages_")

instructions = [
    {
        "simulation_description": "A medieval village in northern britain",
        "num_of_samples": "1",
    }
]

asyncio.run(
    dria.generate(
        inputs=instructions,
        workflow=PersonaBio,
        models=[Model.GEMINI, Model.OPENAI],
        dataset=my_dataset,
        max_tokens=1000,
    )
)

print(my_dataset.get_entries(data_only=True))
