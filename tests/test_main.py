import os
from dria.client import Dria
from dria.pipelines import PipelineConfig
from dria.factory import QAPipeline
import asyncio
import json
import requests


def get_arxiv_context():
    url = "https://r.jina.ai/https://arxiv.org/html/2408.02666v2"

    try:
        # Send GET request
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            # Store the text content in context variable
            context = response.text
            return context
        else:
            print(f"Failed to retrieve content. Status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error occurred while fetching the URL: {e}")
        return None


dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def run_pipeline():
    content = get_arxiv_context()
    lines = [line for line in content.split("\n") if line.strip()]
    chunks = ["\n".join(lines[i : i + 100]) for i in range(0, len(lines), 100)]
    await dria.initialize()

    pipeline = QAPipeline(dria, PipelineConfig(pipeline_timeout=500)).build(
        simulation_description="Grad students who wants to learn about uses cases of the paper",
        num_samples=5,
        persona="A researcher that is concise and direct",
        chunks=chunks,
    )

    result = await pipeline.execute(return_output=True)
    with open("output.json", "w") as f:
        json.dump(result, f, indent=4)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
