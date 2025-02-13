from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import MagPie
import asyncio

my_dataset = DriaDataset(
    collection="magpie_test",
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
        workflows=MagPie,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
