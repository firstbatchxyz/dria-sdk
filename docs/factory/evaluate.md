# EvaluatePrediction

`EvaluatePrediction` is a `Singleton` task that evaluates if a predicted answer is contextually and semantically correct compared to the correct answer.

#### Inputs
- prediction (`str`): The predicted answer to be evaluated.
- question (`str`): The question to compare against.
- context (`str`): The context to compare against.

#### Outputs
- evaluation (`str`): The evaluation result.
- model (`str`): The model used for evaluation.

### Example

Evaluate a prediction based on a question and context. This example uses the default model.

```python
import os
import asyncio
from dria.factory import EvaluatePrediction
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    evaluator = EvaluatePrediction()
    res = await dria.execute(
        Task(
            workflow=evaluator.workflow(
                prediction="The capital of France is Paris.",
                question="What is the capital of France?",
                context="France is a country in Western Europe. Its capital city is Paris."
            ).model_dump(),
            models=[Model.GPT4O]
        ),
        timeout=45,
    )
    return evaluator.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "evaluation":"[correct]",
   "model":"gpt-4o"
}
```