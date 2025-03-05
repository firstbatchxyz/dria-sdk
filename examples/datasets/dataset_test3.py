import asyncio

from dria import Model, Dria, DriaDataset
from dria.workflow.factory import GenerateSubtopics

dria = Dria()

dataset = DriaDataset(collection="test_subtopics")
result = asyncio.run(
    dria.generate(
        inputs=[{"topic": "Artificial Intelligence"}],
        workflow=GenerateSubtopics,
        models=Model.GEMINI,
        dataset=dataset,
    )
)
print(dataset.get_entries(data_only=True))
