from dria import DriaDataset, Model, Dria
from dria.workflow.factory import QA
import asyncio


dria = Dria()
my_dataset = DriaDataset(collection="QA")

inputs = [
    {
        "context": "Structured Outputs is a feature that ensures the model will always generate responses that adhere to your supplied JSON Schema, so you don't need to worry about the model omitting a required key, or hallucinating an invalid enum value.",
        "persona": "A highschool student.",
        "num_questions": 3,
    },
]

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=QA,
        models=[Model.GPT4O],
    )
)


my_dataset.to_jsonl()
