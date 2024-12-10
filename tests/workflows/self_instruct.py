from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import SelfInstruct
import asyncio

my_dataset = DriaDataset(
    name="sinstruct_test",
    description="test",
    schema=SelfInstruct.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "num_instructions":5,
        "criteria_for_query_generation":"Diverse queries related to task management",
        "application_description":"A task management AI assistant",
        "context":"Professional work environment"
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=SelfInstruct,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
