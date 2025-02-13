import json
from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import GenerateSubtopics
import asyncio

my_dataset = DriaDataset(
    name="subtopics",
    description="A dataset for subtopics",
    schema=GenerateSubtopics.OutputSchema,
)
generator = DatasetGenerator(dataset=my_dataset)


instructions = [
    {"topic": "python language"},
    {"topic": "rust language"},
    {"topic": "slack api"},
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=GenerateSubtopics,
        models=[Model.ANTHROPIC_HAIKU_3_5_OR],
    )
)
entries = my_dataset.get_entries(True)

print(json.dumps(entries, indent=2))
