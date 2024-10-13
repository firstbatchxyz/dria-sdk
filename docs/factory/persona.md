# PersonaPipeline


```python
import os
import asyncio
from dotenv import load_dotenv
from dria.factory import PersonaPipeline
from dria.pipelines import PipelineConfig, Pipeline
from dria.client import Dria
import logging

logger = logging.getLogger(__name__)
dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def main(pipeline: Pipeline):
    outputs = await pipeline.execute(return_output=True)
    print(outputs)


if __name__ == "__main__":
    load_dotenv()

    pipeline = PersonaPipeline(dria, PipelineConfig())
    pipeline = pipeline.build(
        simulation_description="Customers of a AI consulting company. Each customer is a business working on a different sector that tries to integrate AI to solve problems.",
        num_samples=5)
    asyncio.run(main(pipeline))
```