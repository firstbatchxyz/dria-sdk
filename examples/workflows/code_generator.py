from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import GenerateCode
import asyncio

my_dataset = DriaDataset(
    name="code", description="A dataset for code", schema=GenerateCode.OutputSchema
)

generator = DatasetGenerator(dataset=my_dataset)


instructions = [
    {
        "instruction": "Write a function to calculate the factorial of a number",
        "language": "python",
    },
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=GenerateCode,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
