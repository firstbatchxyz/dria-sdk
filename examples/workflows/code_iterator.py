from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import IterateCode
import asyncio

my_dataset = DriaDataset(
    name="code_it_test",
    description="A dataset for code",
    schema=IterateCode.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "code": """
    def greet(name):
        print("Hello, " + name)
    """,
        "instruction": "Add error handling for empty name input",
        "language": "python",
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=IterateCode,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
