from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import EvolveInstruct
import asyncio

my_dataset = DriaDataset(
    name="evolve_i_test",
    description="test",
    schema=EvolveInstruct.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "prompt": "Explain the concept of photosynthesis.",
        "mutation_type": "DEEPEN",
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=EvolveInstruct,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
