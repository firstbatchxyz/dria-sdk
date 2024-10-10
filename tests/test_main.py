import asyncio
from typing import Dict, Any
from dria.factory import (
    TextMatching,
    PersonaPipeline,
    SubTopicPipeline,
    SelfInstruct,
    WebFactCheck,
    Clair,
    GenerateGraph,
    ScoreComplexity,
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
    cl = WebFactCheck(num_queries=2)
    wf = cl.workflow(
        context="A 16-year-old boy with a seizure disorder and cognitive delay is brought to the physician because of progressively worsening right lower extremity weakness for the past 6 months. He does not make eye contact and sits very close to his mother. Physical examination shows a grade 3/6 holosystolic murmur at the cardiac apex. Neurological examination shows decreased strength in the right lower leg with normal strength in the other extremities. Fundoscopic examination shows several multinodular, calcified lesions in the retina bilaterally. A photograph of his skin findings is shown. This patient's condition is most likely due to a mutation in which of the following?"
    )
    print(wf.model_dump_json(exclude_none=True, exclude_unset=True))
    res = await dria.execute(
        Task(
            workflow=cl.workflow(
                num_instructions=5,
                criteria_for_query_generation="Queries should be multi-step and complex.",
                application_description="A chatbot that helps users with their mental health.",
                context="Someone struggling with anxiety.",
            ).model_dump(),
            models=[Model.LLAMA3_1_8B_FP16],
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
