# EvolveQuality

`EvolveQuality` is a `SingletonTemplate` task that evolves the quality of a response to a prompt through rewriting based on a specified method.

#### Inputs
- prompt (`str`): The original prompt.
- response (`str`): The original response to be evolved.
- method (`str`): The method for evolving the response. Must be one of the following:
  - `"HELPFULNESS"`
  - `"RELEVANCE"`
  - `"DEEPENING"`
  - `"CREATIVITY"`
  - `"DETAILS"`

#### Outputs
- response (`str`): The original response.
- evolved_response (`str`): The evolved version of the original response.
- method (`str`): The method used for evolution.
- model (`str`): The model used for generation.

### Example

Evolve a response using the "DEEPENING" method. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import EvolveQuality
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    evolve_quality = EvolveQuality()
    original_prompt = "Explain the concept of photosynthesis."
    original_response = "Photosynthesis is the process by which plants make their own food using sunlight."
    
    res = await dria.execute(
        Task(
            workflow=evolve_quality.workflow(prompt=original_prompt, response=original_response, method="DEEPENING").model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return evolve_quality.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "response":"Photosynthesis is the process by which plants make their own food using sunlight.",
   "evolved_response":"Photosynthesis is a complex biochemical process through which plants, algae, and some bacteria convert light energy into chemical energy. This process occurs in the chloroplasts of plant cells and involves two main stages: the light-dependent reactions and the light-independent reactions (Calvin cycle). During the light-dependent reactions, chlorophyll and other pigments in the thylakoid membranes absorb sunlight, which drives the splitting of water molecules into oxygen, protons, and electrons. This creates a proton gradient that powers the production of ATP. The light-independent reactions use the energy from ATP and NADPH (produced in the light-dependent reactions) to fix carbon dioxide from the air into glucose through a series of enzymatic reactions. This glucose serves as the primary energy source for the plant and can be used to synthesize other organic compounds necessary for growth and development. Photosynthesis is crucial for life on Earth, as it produces oxygen as a byproduct and forms the base of most food chains in ecosystems.",
   "method":"DEEPENING",
   "model":"gemma2:9b-instruct-fp16"
}
```

#### References
- [EvolInstruct Distilabel](https://distilabel.argilla.io/latest/components-gallery/tasks/evolquality/)
- [What Makes Good Data for Alignment? A Comprehensive Study of Automatic Data Selection in Instruction Tuning](https://arxiv.org/abs/2312.15685)