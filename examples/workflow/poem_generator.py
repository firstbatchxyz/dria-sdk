"""
Poem Generator Example

This script demonstrates how to use the Dria SDK to generate poems based on user prompts.
It showcases the asynchronous workflow for task creation, execution, and result retrieval.

"""

import asyncio
import logging

from dria.client import Dria
from dria.models import Task
from dria.models.enums import Model
from dria.workflows.lib.poem_generator import poem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Dria client
dria = Dria()


async def generate_poem(prompt: str):
    task = Task(
        workflow=poem(prompt),
        models=[
            Model.GPT4O,
            Model.LLAMA3_1_8B_FP16,
            Model.GEMMA2_9B,
            Model.GEMMA2_9B_FP16,
            Model.QWEN2_5_7B_FP16,
        ]
    )
    await dria.push(task)
    return task


async def main():
    await dria.initialize()

    prompt = "Write a poem about love"
    node_count = 1

    logger.info(f"Generating {node_count} poem(s) based on the prompt: '{prompt}'")
    tasks = [await generate_poem(prompt) for _ in range(3)]
    results = await dria.fetch(task=tasks)
    print(results)

    for i, result in enumerate(results, 1):
        print(f"\nPoem {i}:")
        print("-" * 60)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
