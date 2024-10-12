# EvolveInstruct

`EvolveInstruct` is a `SingletonTemplate` task that mutates a given prompt based on a specified mutation type.

#### Inputs
- prompt (`str`): The original prompt to be mutated.
- mutation_type (`MutationType`): The type of mutation to apply. Must be one of the following:
  - `"FRESH_START"`
  - `"ADD_CONSTRAINTS"`
  - `"DEEPEN"`
  - `"CONCRETIZE"`
  - `"INCREASE_REASONING"`
  - `"SWITCH_TOPIC"`

#### Outputs
- mutated_prompt (`str`): The mutated version of the original prompt.
- prompt (`str`): The original input prompt.
- model (`str`): The model used for generation.

### Example

Mutate a prompt using the "DEEPEN" mutation type. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import EvolveInstruct
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    evolve_instruct = EvolveInstruct()
    original_prompt = "Explain the concept of photosynthesis."
    
    res = await dria.execute(
        Task(
            workflow=evolve_instruct.workflow(prompt=original_prompt, mutation_type="DEEPEN").model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return evolve_instruct.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "mutated_prompt":"**Discuss the intricate process of photosynthesis, delving into its two main stages (light-dependent and light-independent reactions).  Explain how sunlight is captured, water is split, and carbon dioxide is fixed to produce glucose, the primary energy source for plants. Describe the role of chlorophyll and other pigments in absorbing light energy, and outline the significance of photosynthesis for life on Earth, including its impact on oxygen production and the global carbon cycle.** \n\n\nThis new prompt:\n\n* **Increases depth:** It asks for a more detailed explanation, including the two stages of photosynthesis and their specific mechanisms.\n* **Increases breadth:**  It expands the scope to include the roles of chlorophyll, pigments, and the broader ecological significance of photosynthesis.",
   "prompt":"Explain the concept of photosynthesis.",
   "model":"gemma2:9b-instruct-fp16"
}
```