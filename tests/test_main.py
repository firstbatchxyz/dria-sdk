import asyncio
import os

from dria.client import Dria
from dria.factory import SearchPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = SearchPipeline(dria, PipelineConfig(pipeline_timeout=80)).build(
        topic="Journalism in Turkey.", summarize=True
    )
    res = await pipeline.execute(return_output=True)
    with open("search_results.json", "w") as f:
        f.write(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
