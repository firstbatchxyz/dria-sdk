import asyncio
from typing import Dict, Any
from dria.factory import (
    TextMatching,
    PersonaPipeline,
    SubTopicPipeline,
    evaluate_prediction,
    magpie_instruct,
    Clair,
    GenerateGraph,
    ScoreComplexity,
    DialoguePipeline,
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
    cl = TextMatching()
    res = await dria.execute(
            Task(
                workflow=cl.workflow(
                    task_description="Classify airline tweets into positive, negative, or neutral sentiment.",
                    language="en",
                ).model_dump(),
                models=[Model.QWEN2_5_7B_FP16],
            ),
            timeout=90,
        )
    print(cl.parse_result(res))






if __name__ == "__main__":

    load_dotenv()

    cfg = PipelineConfig()
    """
    pipe = DialoguePipeline(dria, cfg).build(
        instructor_persona="A patient that has problems with her knees while running. Your communications are direct and concise. You wan't get better soon.",
        responding_persona="You are expert MD working on a hospital. Your are helpful and good at understanding patient needs.",
        num_turns=2,
        speakers=["Patient", "Doctor"],
    )
    """
    asyncio.run(evaluate())
