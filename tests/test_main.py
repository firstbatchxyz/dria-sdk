import asyncio
from typing import Dict, Any
from dria.factory import (
    score_complexity,
    evolve_complexity,
    generate_semantic_triple,
    PersonaPipeline,
    SubTopicPipeline,
    evaluate_prediction,
    magpie_instruct,
)
import os
from dotenv import load_dotenv

from dria.client import Dria
from dria.models import Task, Model
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


async def evaluate():
    "te"
    print(
        await dria.execute(
            Task(
                workflow=magpie_instruct(
                    instructor_persona="A patient that has problems with her knees while running. Your communications are direct and concise. You wan't get better soon.",
                    responding_persona="You are expert MD working on a hospital. Your are helpful and good at understanding patient needs.",
                    num_turns=1,
                ).model_dump(),
                models=[Model.LLAMA3_1_8B_FP16],
            )
        )
    )


if __name__ == "__main__":

    load_dotenv()

    cfg = PipelineConfig()
    """
    pipe = PersonaPipeline(dria, cfg).build(
        simulation_description="Doctors that work in a hospital in cuba. Each coming from a different background, some not cuban. "
        "They work on different domains. Some are novice, some are experts.",
        num_samples=2,
    )
    """

    asyncio.run(evaluate())
