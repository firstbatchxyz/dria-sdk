from dria import DriaDataset, Model, Dria
from dria.workflow.factory import EvolveInstruct
import asyncio

from dria.workflow.factory.workflows.evol_instruct.task import MUTATION_TEMPLATES

my_dataset = DriaDataset(
    collection="evolve_i_test",
)

dria = Dria()

params = {
        "prompt": "Explain the concept of photosynthesis.",
        "mutation_type": "DEEPEN",
    }

inputs = MUTATION_TEMPLATES[params["mutation_type"]].format("{{prompt}}", params["prompt"])
print(asyncio.run(
    dria.generate(
        inputs=inputs,
        workflow=EvolveInstruct,
        models=Model.GEMINI
    )
))
