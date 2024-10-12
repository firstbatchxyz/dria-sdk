# EvolveComplexity

`EvolveComplexity` is a `Singleton` task that increases the complexity of a given instruction.

#### Inputs
- instruction (`str`): The original instruction to be evolved.

#### Outputs
- evolved_instruction (`str`): The more complex version of the original instruction.
- instruction (`str`): The original instruction.
- model (`str`): The model used for generation.

### Example

Increase the complexity of a given instruction. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import EvolveComplexity
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    evolve = EvolveComplexity()
    res = await dria.execute(
        Task(
            workflow=evolve.workflow(instruction="Write a short story about a cat.").model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return evolve.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "evolved_instruction":"Write a short story about a cat who, unbeknownst to its human family, communicates with other cats in a secret language that revolves around solving mysteries within the neighborhood. The cat must navigate between two worlds: the simple life of domesticity and the complex web of feline intrigue, all while trying not to reveal their dual life to their human companions.",
   "instruction":"Write a short story about a cat.",
   "model":"qwen2.5:32b-instruct-fp16"
}
```