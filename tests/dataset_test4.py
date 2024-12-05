import asyncio
from dria import Prompt, DatasetGenerator, DriaDataset, Model
from pydantic import BaseModel, Field


class Poem(BaseModel):
    topic: str = Field(..., title="Topic")
    poem: str = Field(..., title="Poem")


dataset = DriaDataset(name="test4", description="test4", schema=Poem)

instructions = [{"topic": "Roses"}, {"topic": "Decentralized synthetic data"}]

prompter = Prompt(prompt="Write a poem about {{topic}}", schema=Poem)
generator = DatasetGenerator(dataset=dataset)

asyncio.run(
    generator.generate_data(
        instructions=instructions, singletons=prompter, models=[Model.GPT4O]
    )
)


print(dataset.to_pandas())
