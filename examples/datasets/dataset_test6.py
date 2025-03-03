import asyncio

from dria import DriaDataset, Dria
from dria.workflow.factory import SearchWeb

dria = Dria()
my_dataset = DriaDataset(collection="searches")

inputs = [
    {"query": "Istanbul'daki en iyi kebapçılar", "lang": "tr", "n_results": 5},
    {"query": "Best kebap places in Istanbul", "lang": "en", "n_results": 5},
]

asyncio.run(dria.generate(inputs=inputs, workflow=SearchWeb, dataset=my_dataset))

my_dataset.to_jsonl()
