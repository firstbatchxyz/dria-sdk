import asyncio
import os

from dria.client import Dria
from dria.factory import PersonaPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = PersonaPipeline(dria, PipelineConfig()).build(
        simulation_description="The cyberpunk city in the year of 2077.", num_samples=2
    )
    res = await pipeline.execute(return_output=True)
    print(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
