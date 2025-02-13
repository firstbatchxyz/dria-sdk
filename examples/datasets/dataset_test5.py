import asyncio

from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import PersonaBio

my_dataset = DriaDataset(
    name="pages",
    description="A dataset for pages",
    schema=PersonaBio[-1].OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {
        "simulation_description": "A medieval village in northern britain",
        "num_of_samples": 8,
    },
    {"simulation_description": "A modern neo-tokio", "num_of_samples": 5},
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=PersonaBio,
        models=[
            [Model.ANTHROPIC_HAIKU_3_5_OR, Model.QWEN2_5_72B_OR],
            [
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA_3_1_8B_OR,
                Model.QWEN2_5_7B_OR,
            ],
        ],
    )
)

my_dataset.to_jsonl()
