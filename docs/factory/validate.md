# ValidatePrediction

`ValidatePrediction` is a `Singleton` task that determines if a predicted answer is contextually and semantically correct compared to a given correct answer.

#### Inputs
- prediction (`str`): The predicted answer to be evaluated.
- correct_answer (`str`): The correct answer to compare against.

#### Outputs
- validation (`bool`): True if the prediction is correct, False otherwise.
- model (`str`): The model used for validation.

### Example

Validate a prediction against a correct answer. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import ValidatePrediction
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    validate_prediction = ValidatePrediction()
    res = await dria.execute(
        Task(
            workflow=validate_prediction.workflow(
                prediction="The capital of France is Paris.",
                correct_answer="Paris is the capital city of France."
            ).model_dump(),
            models=[Model.QWEN2_5_32B_FP16],
        ),
        timeout=45,
    )
    return validate_prediction.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
  "validation": true, 
  "model": "qwen2.5:32b-instruct-fp16"
}
```