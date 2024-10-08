import asyncio

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
    await pipeline.execute()

    while True:
        state, status, output = pipeline.poll()
        if output:
            logger.info("Pipeline execution completed successfully.")
            logger.info(f"Output: {output}")
            break
        else:
            logger.debug(f"Pipeline status: {status}. Current state: {state}")
            await asyncio.sleep(5)

if __name__ == "__main__":

    load_dotenv()

    cfg = PipelineConfig()
    pipe = SubTopicPipeline(dria, cfg).build(topics=["Artificial Intelligence"], max_depth=2)

    asyncio.run(main(pipe))
