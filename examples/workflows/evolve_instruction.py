from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import EvolveInstruct
import asyncio

my_dataset = DriaDataset(
    collection="evolve_i_test",
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
        workflows=EvolveInstruct,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
