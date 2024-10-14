import asyncio
import os

from dria.client import Dria
from dria.factory import SearchPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = SearchPipeline(dria, PipelineConfig(pipeline_timeout=50)).build(
        topic="Journalism in Turkey."
    )
    res = await pipeline.execute(return_output=True)
    print(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
