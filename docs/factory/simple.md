# Simple

`Simple` is a `Singleton` task that generates text based on instruction.


#### Inputs
- prompt (`str`): The prompt to generate text from.

#### Outputs
- text: (`str`): The generated text.


### Example

Generate text based on prompt. This examples uses `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import Simple
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    simple = Simple()
    res = await dria.execute(
        Task(
            workflow=simple.workflow(prompt="Hey there!").model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return simple.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()

```

Expected output:

```bash
2024-10-12 17:23:58,912 - INFO - Address 2ca170738d7178ecd3f1264e46c175be6469dbd1 added to blacklist with deadline at 1728743638.
2024-10-12 17:23:58,912 - INFO - Task N3cyBA9hWczmHHNnzltn6DEyqYMthkDf successfully published. Step: 
2024-10-12 17:24:05,004 - INFO - Address 2ca170738d7178ecd3f1264e46c175be6469dbd1 removed from blacklist.
2024-10-12 17:24:05,920 - INFO - Background tasks cancelled.
Hey there! 👋 What can I do for you today? 😊  
```