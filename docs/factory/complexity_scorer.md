# ScoreComplexity

`ScoreComplexity` is a `Singleton` task that ranks a list of instructions based on their complexity.

#### Inputs
- instructions (`List[str]`): A list of instructions to be ranked.

#### Outputs
- scores (`str`): A string containing the complexity scores for each instruction.

### Example

Rank a list of instructions based on complexity. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import ScoreComplexity
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    score_complexity = ScoreComplexity()
    instructions = [
        "Boil water in a kettle",
        "Write a research paper on quantum physics",
        "Tie your shoelaces",
        "Develop a machine learning algorithm",
        "Make a sandwich"
    ]
    res = await dria.execute(
        Task(
            workflow=score_complexity.workflow(instructions=instructions).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return score_complexity.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
[
   {
      "instruction":"Boil water in a kettle",
      "score":3,
      "model":"llama3.1:8b-instruct-fp16"
   },
   {
      "instruction":"Write a research paper on quantum physics",
      "score":5,
      "model":"llama3.1:8b-instruct-fp16"
   },
   {
      "instruction":"Tie your shoelaces",
      "score":4,
      "model":"llama3.1:8b-instruct-fp16"
   },
   {
      "instruction":"Develop a machine learning algorithm",
      "score":5,
      "model":"llama3.1:8b-instruct-fp16"
   },
   {
      "instruction":"Make a sandwich",
      "score":2,
      "model":"llama3.1:8b-instruct-fp16"
   }
]
```

#### References
- [ComplexityScorer Distilabel](https://distilabel.argilla.io/latest/components-gallery/tasks/complexityscorer)
- [What Makes Good Data for Alignment? A Comprehensive Study of Automatic Data Selection in Instruction Tuning](https://arxiv.org/abs/2312.15685)
- 