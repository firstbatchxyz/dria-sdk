import asyncio

from dria import DriaDataset, Model, Dria
from dria.workflow.factory import EvolveQuality
from dria.workflow.factory.workflows.evol_quality.task import MUTATION_TEMPLATES

my_dataset = DriaDataset(
    collection="evolve_q_test"
)

dria = Dria()

inputs = [
    {
        "prompt": "Explain the concept of photosynthesis.",
        "response": "Photosynthesis is the process by which plants make their own food using sunlight.",
        "method": MUTATION_TEMPLATES["DEEPENING"],
    }
]

asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=EvolveQuality,
        models=Model.GPT4O,
    )
)

print(my_dataset.get_entries(data_only=True))
