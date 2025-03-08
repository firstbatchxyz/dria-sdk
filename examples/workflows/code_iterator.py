import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import IterateCode

my_dataset = DriaDataset(
    collection="code_it_test",
)

inputs = [
    {
        "code": """
    def greet(name):
        print("Hello, " + name)
    """,
        "instruction": "Add error handling for empty name input",
        "language": "python",
    }
]

dria = Dria()

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=IterateCode,
        models=Model.GEMINI,
        dataset=my_dataset
    )
)

print(my_dataset.get_entries(data_only=True))
