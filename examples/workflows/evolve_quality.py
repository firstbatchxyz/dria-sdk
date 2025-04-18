from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import EvolveQuality
import asyncio
from dria.factory.workflows.evol_quality.task import MUTATION_TEMPLATES

my_dataset = DriaDataset(
    name="evolve_q_test",
    description="test",
    schema=EvolveQuality.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "prompt": "Explain the concept of photosynthesis.",
        "response": "Photosynthesis is the process by which plants make their own food using sunlight.",
        "method": MUTATION_TEMPLATES["DEEPENING"],
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=EvolveQuality,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
