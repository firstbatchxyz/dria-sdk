import os
from dria.client import Dria
import asyncio
import json
from examples.nvidias_preference_data_pipeline.nemotron_qa import NemotronQA

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def run_pipeline():

    await dria.initialize()
    pipeline = NemotronQA(dria).build(
        topic="Machine Learning", n_subtopics="10", n_questions="5"
    )

    result = await pipeline.execute(return_output=True)
    with open("output.json", "w") as f:
        json.dump(result, f, indent=4)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
