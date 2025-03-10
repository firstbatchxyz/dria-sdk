from dria import DriaDataset, Model, Dria
from dria.workflow.factory import MagPie
import asyncio

my_dataset = DriaDataset(collection="magpie_test")

dria = Dria()

instructions = [
    {
        "instructor_persona": "Researcher on quantum computing at @Google",
        "responding_persona": "An AI assistant",
        "num_turns": "3",
    }
]


asyncio.run(
    dria.generate(
        inputs=instructions,
        workflow=MagPie,
        models=Model.OPENROUTER,
        dataset=my_dataset
    )
)

print(my_dataset.get_entries(data_only=True))
