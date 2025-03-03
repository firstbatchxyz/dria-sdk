import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import PersonaBio

dria = Dria()
my_dataset = DriaDataset(collection="pages")

instructions = [
    {
        "simulation_description": "A medieval village in northern britain",
        "num_of_samples": 8,
    },
    {"simulation_description": "A modern neo-tokio", "num_of_samples": 5},
]

asyncio.run(
    dria.generate(
        inputs=instructions,
        workflow=PersonaBio,
        models=[
            [Model.ANTHROPIC_HAIKU_3_5_OR, Model.QWEN2_5_72B_OR],
            [
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA_3_1_8B_OR,
                Model.QWEN2_5_7B_OR,
            ],
        ],
        dataset=my_dataset,
    )
)

my_dataset.to_jsonl()
