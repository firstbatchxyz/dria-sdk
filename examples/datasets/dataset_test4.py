import asyncio
import logging

from dria import Prompt, DatasetGenerator, DriaDataset, Model
from pydantic import BaseModel, Field


# Define output schema
class Tweet(BaseModel):
    topic: str = Field(..., title="Topic")
    tweet: str = Field(..., title="tweet")


# Create dataset
dataset = DriaDataset(
    name="tweet_test", description="A dataset of tweets!", schema=Tweet
)

instructions = [{"topic": "BadBadNotGood"}, {"topic": "Decentralized synthetic data"}]

prompter = Prompt(prompt="Write a tweet about {{topic}}", schema=Tweet)
generator = DatasetGenerator(dataset=dataset, log_level=logging.DEBUG)

asyncio.run(
    generator.generate(
        instructions=instructions, workflows=prompter, models=Model.OPENAI
    )
)


print(dataset.to_pandas())
