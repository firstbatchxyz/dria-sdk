from dria import DriaDataset, Model, Dria
from dria.workflow.factory import InstructionBacktranslation
import asyncio

my_dataset = DriaDataset(
    collection="instruction_backtranslation_test",
)

dria = Dria()

inputs = [
    {
        "instruction": "What is 3 times 20?",
        "generation": "It's 60.",
    }
]

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=InstructionBacktranslation,
        models=Model.OPENROUTER,
        dataset=my_dataset,
    )
)

print(my_dataset.get_entries(data_only=True))
