# Batches


## Overview


```python
from dria.client import Dria
from dria.factory import Simple
from dria.batches import ParallelSingletonExecutor
import asyncio

async def main():
    dria_client = Dria()
    singleton = Simple()
    executor = ParallelSingletonExecutor(dria_client, singleton, batch_size=100)
    executor.load_instructions([{ "prompt": "What is the capital of France?" }, { "prompt": "What is the capital of Germany?" }])
    results = await executor.run()
    print(results)

asyncio.run(main())
```