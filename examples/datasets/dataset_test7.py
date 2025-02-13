from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import QA
import asyncio

my_dataset = DriaDataset(
    collection="QA",
    schema=QA[-1].OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)


instructions = [
    {
        "context": "Structured Outputs is a feature that ensures the model will always generate responses that adhere to your supplied JSON Schema, so you don't need to worry about the model omitting a required key, or hallucinating an invalid enum value.",
        "persona": "A highschool student.",
        "num_questions": 3,
    },
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=QA,
        models=[Model.GPT4O],
    )
)


my_dataset.to_jsonl()
