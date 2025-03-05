import asyncio

from dria import DriaDataset, Model, Dria

dria = Dria()
dataset = DriaDataset(collection="tweet_test")

instructions = [
    "Write a tweet about BadBadNotGood",
    "Write a tweet about Decentralized synthetic data",
]

asyncio.run(dria.generate(
    inputs="Write a tweet about {{topic}}",
    models=Model.OPENAI,
    dataset=dataset)
)

print(dataset.to_pandas())
