from dria import DriaDataset, Model, Dria
from dria.workflow.factory import ValidatePrediction
import asyncio

my_dataset = DriaDataset(
    collection="evalpred_test",
)

dria = Dria()
inputs = [
    {
        "prediction": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and tracking completion status",
        "correct_answer": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and monitoring progress",
    }
]

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=ValidatePrediction,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
