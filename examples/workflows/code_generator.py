import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import GenerateCode

my_dataset = DriaDataset(collection="code")

inputs = [
    {
        "instruction": "Write a function to calculate the factorial of a number",
        "language": "python",
    },
]

dria = Dria()

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=GenerateCode,
        models=Model.GEMINI,
    )
)

print(my_dataset.get_entries(data_only=True))
