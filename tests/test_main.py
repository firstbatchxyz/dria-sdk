import asyncio
import os

from dria.client import Dria
from dria.factory import SubTopicPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = SubTopicPipeline(dria, PipelineConfig()).build(
        topic="Artificial Intelligence", max_depth=2
    )
    res = await pipeline.execute(return_output=True)
    print(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
