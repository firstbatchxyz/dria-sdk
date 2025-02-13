from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import InstructionBacktranslation
import asyncio

my_dataset = DriaDataset(
    name="instruction_backtranslation_test",
    description="test",
    schema=InstructionBacktranslation.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "instruction": "What is 3 times 20?",
        "generation": "It's 60.",
    }
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=InstructionBacktranslation,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
