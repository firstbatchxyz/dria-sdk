from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import EvaluatePrediction
import asyncio

my_dataset = DriaDataset(
    collection="evalpred_test",
    schema=EvaluatePrediction.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "prediction": "The AI assistant will help with task management by providing features like task creation, scheduling, prioritization, reminders, and progress tracking.",
        "question": "What capabilities will the AI assistant provide for task management?",
        "context": "Professional work environment",
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=EvaluatePrediction,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
