import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import EvaluatePrediction

my_dataset = DriaDataset(
    collection="evalpred_test",
)

inputs = [
    {
        "prediction": "The AI assistant will help with task management by providing features like task creation, scheduling, prioritization, reminders, and progress tracking.",
        "question": "What capabilities will the AI assistant provide for task management?",
        "context": "Professional work environment",
    }
]

dria = Dria()

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=EvaluatePrediction,
        models=Model.GEMINI,
        dataset=my_dataset,
    )
)

print(my_dataset.get_entries(data_only=True))
