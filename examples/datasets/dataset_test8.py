from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import Simple
import asyncio

my_dataset = DriaDataset(
    name="simple",
    description="A simple dataset",
    schema=Simple.OutputSchema,
)
generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {"prompt": "Write a haiku about open source AI."},
]
asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=Simple,
        models=Model.LLAMA_3_1_8B_OR,
    )
)
my_dataset.to_json()
