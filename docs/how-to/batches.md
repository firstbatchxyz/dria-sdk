# Batches

Batches (ParallelSingletonExecutor) is a way to run multiple instructions in parallel. 
This is useful when you have a large number of instructions to run and you want to run them concurrently.

To use Batches, you need to create a `Dria` client, a `Singleton` task, and a `ParallelSingletonExecutor` object.

```python
from dria.client import Dria
from dria.factory import Simple
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
import asyncio

async def batch():
    dria_client = Dria()
    singleton = Simple()
    executor = ParallelSingletonExecutor(dria_client, singleton)
    executor.set_models([Model.QWEN2_5_7B_FP16, Model.LLAMA3_2_3B, Model.LLAMA3_2_1B])
    executor.load_instructions([{ "prompt": "What is the capital of France?" }, { "prompt": "What is the capital of Germany?" }])
    return await executor.run()

def main():
    results = asyncio.run(batch())
    print(results)

if __name__ == "__main__":
    main()
```

Instructions are passed to the `executor` using the `load_instructions` method.
Format of the instructions should match the input format of the `Singleton` task.


