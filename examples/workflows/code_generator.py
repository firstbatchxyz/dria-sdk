from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import GenerateCode
import asyncio

my_dataset = DriaDataset(collection="code", schema=GenerateCode.OutputSchema)

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
        workflows=GenerateCode,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
