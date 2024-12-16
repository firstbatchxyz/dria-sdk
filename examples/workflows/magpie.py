from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import MagPie
import asyncio

my_dataset = DriaDataset(
    name="magpie_test",
    description="test",
    schema=MagPie.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "instructor_persona": "Researcher on quantum computing at @Google",
        "responding_persona": "An AI assistant",
        "num_turns": 3,
    }
]


asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=MagPie,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
