# SelfInstruct

`SelfInstruct` is a `Singleton` task that generates user queries for a given AI application and context.

#### Inputs
- num_instructions (`int`): The number of user queries to generate.
- criteria_for_query_generation (`str`): The criteria for generating the queries.
- application_description (`str`): A description of the AI application.
- context (`str`): The context to which the queries should be applicable.

#### Outputs
- instructions (`List[str]`): The generated user queries.
- model (`str`): The model used for generation.

### Example

Generate user queries for an AI application. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import SelfInstruct
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    self_instruct = SelfInstruct()
    res = await dria.execute(
        Task(
            workflow=self_instruct.workflow(
                num_instructions=5,
                criteria_for_query_generation="Diverse queries related to task management",
                application_description="A task management AI assistant",
                context="Professional work environment"
            ).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return self_instruct.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "instructions":[
      "Prioritize my upcoming deadlines, considering project dependencies. ",
      "Can you schedule a meeting with the marketing team for next week to discuss the Q3 campaign?",
      "Generate a comprehensive list of actionable steps required for completing the client proposal.",
      "What tasks are currently assigned to me that are due within the next 7 days?",
      "Remind me to follow up with John about the budget approval at 2 PM tomorrow."
   ],
   "model":"gemma2:9b-instruct-fp16"
}
```