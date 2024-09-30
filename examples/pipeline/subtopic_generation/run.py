import asyncio
import logging
import os

from dria.client import Dria
from pipeline import create_subtopic_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
dria = Dria()


async def main():

    topic = "Artificial Intelligence"
    logger.info(f"Creating pipeline for topic: {topic}")
    await dria.initialize()
    for i in range(10):
        try:
            main_pipeline = await create_subtopic_pipeline(dria, topic)
            await main_pipeline.execute()
            logger.info("Pipeline execution started successfully.")
        except Exception as e:
            logger.error(f"Error during pipeline setup or execution: {str(e)}")
            return

        while True:
            state, status, output = main_pipeline.poll()
            if output:
                logger.info("Pipeline execution completed successfully.")
                break
            else:
                logger.debug(f"Pipeline status: {status}. Current state: {state}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
