import json

from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import SemanticTriplet
import asyncio

my_dataset = DriaDataset(
    name="triplets",
    description="A dataset of semantic triplets",
    schema=SemanticTriplet.OutputSchema,
)
generator = DatasetGenerator(dataset=my_dataset)


instructions = [
    {
        "unit": "sentence",
        "language": "tr",
        "low_score": 1,
        "high_score": 5,
        "difficulty": "college",
    },
    {
        "unit": "sentence",
        "language": "tr",
        "low_score": 1,
        "high_score": 5,
        "difficulty": "highschool",
    },
]


asyncio.run(
    generator.generate_dataset(
        instructions=instructions,
        singletons=SemanticTriplet,
        models=[Model.QWEN2_5_72B_OR],
    )
)
entries = my_dataset.get_entries(True)

print(json.dumps(entries, indent=2))
