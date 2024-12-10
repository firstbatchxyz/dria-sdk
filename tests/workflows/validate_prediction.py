from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import ValidatePrediction
import asyncio

my_dataset = DriaDataset(
    name="evalpred_test",
    description="test",
    schema=ValidatePrediction.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)
instructions = [
    {
        "prediction": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and tracking completion status",
        "correct_answer": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and monitoring progress", 
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=ValidatePrediction,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
