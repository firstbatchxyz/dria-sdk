import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import Clair

my_dataset = DriaDataset(
    collection="clair_test",
)

dria = Dria()

asyncio.run(
    dria.generate(
        inputs=[
            {
                "task": "Math",
                "student_solution": "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
            },
        ],
        workflow=Clair,
        models=Model.GEMINI,
        dataset=my_dataset,
    )
)

print(my_dataset.get_entries(data_only=True))
