import asyncio

from dria import Model, Dria
from dria.workflow.factory import EvolveQuality
from dria.workflow.factory.workflows.evol_quality.task import MUTATION_TEMPLATES

dria = Dria()

inputs = [
    {
        "prompt": "Explain the concept of photosynthesis.",
        "response": "Photosynthesis is the process by which plants make their own food using sunlight.",
        "method": MUTATION_TEMPLATES["DEEPENING"],
    }
]

print(asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=EvolveQuality,
        models=Model.GEMINI,
    )
))

