import asyncio
import os
import json
from dria.client import Dria
from dria.factory import SearchPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token="78dd9baa-ff7c-4033-902d-98ef02861268")

async def evaluate():
    await dria.initialize()
    pipeline = SearchPipeline(dria, PipelineConfig(pipeline_timeout=80)).build(
        topic="Entropy-based sampling", summarize=True
    )
    res = await pipeline.execute(return_output=True)
    with open("search_results.json", "w") as f:
        f.write(json.dumps(res, indent=2))


if __name__ == "__main__":
    asyncio.run(evaluate())