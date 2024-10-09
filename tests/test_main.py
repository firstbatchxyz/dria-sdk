import asyncio
from typing import Dict, Any
from dria.factory import (
    score_complexity,
    evolve_complexity,
    generate_semantic_triple,
    PersonaPipeline,
    SubTopicPipeline,
)
import os
from dotenv import load_dotenv

from dria.client import Dria
from dria.pipelines import PipelineConfig, Pipeline
import logging

logger = logging.getLogger(__name__)
dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def main(pipeline: Pipeline):
    await dria.initialize()
    print("Executing pipeline")
    result = await pipeline.execute()
    print(result)
    return


if __name__ == "__main__":

    load_dotenv()

    cfg = PipelineConfig()
    pipe = PersonaPipeline(dria, cfg).build(
        simulation_description="Doctors that work in a hospital in cuba. Each coming from a different background, some not cuban. "
        "They work on different domains. Some are novice, some are experts.",
        num_samples=2,
    )

    asyncio.run(main(pipe))
