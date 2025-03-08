from dria import DriaDataset, Model, Dria
from dria.workflow.factory import SelfInstruct
import asyncio

my_dataset = DriaDataset(collection="sinstruct_test")

dria = Dria()

inputs = [
    {
        "num_instructions": 5,
        "criteria_for_query_generation": "Diverse queries related to task management",
        "application_description": "A task management AI assistant",
        "context": "Professional work environment",
    }
]

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=SelfInstruct,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
