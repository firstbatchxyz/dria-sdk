import asyncio

from dria import DriaDataset, DatasetGenerator
from dria.workflow.factory import SearchWeb

my_dataset = DriaDataset(
    collection="searches",
    schema=SearchWeb.OutputSchema,
)

generator = DatasetGenerator(dataset=my_dataset)

instructions = [
    {"query": "Istanbul'daki en iyi kebapçılar", "lang": "tr", "n_results": 5},
    {"query": "Best kebap places in Istanbul", "lang": "en", "n_results": 5},
]

asyncio.run(
    generator.generate(
        instructions=instructions,
        workflows=SearchWeb,
    )
)

my_dataset.to_jsonl()
