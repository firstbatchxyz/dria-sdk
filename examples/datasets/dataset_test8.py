import asyncio

from dria import DriaDataset, Model, Dria

dria = Dria()
my_dataset = DriaDataset(collection="simple")

asyncio.run(
    dria.generate(
        inputs="Write a haiku about open source AI.",
        models=Model.LLAMA_3_1_8B_OR,
        dataset=my_dataset,
    )
)
my_dataset.to_json()
