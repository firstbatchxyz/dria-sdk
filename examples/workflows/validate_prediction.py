from dria import DriaDataset, Model, Dria
from dria.workflow.factory import ValidatePrediction
import asyncio

my_dataset = DriaDataset(
    collection="evalpred_test",
)

dria = Dria()


async def main():
    await dria.check_model_availability()
    inputs = [
        {
            "prediction": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and tracking completion status",
            "correct_answer": "Task management capabilities include creating tasks, setting deadlines, organizing priorities, and monitoring progress",
        }
    ]
    return await dria.generate(
        inputs=inputs,
        workflow=ValidatePrediction,
        models=Model.GEMINI,
    )


asyncio.run(main())
print(my_dataset.get_entries(data_only=True))
