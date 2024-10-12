# WebFactCheck

`WebFactCheck` is a `SingletonTemplate` task that performs web-based fact-checking on a given context.

#### Inputs
- context (`str`): The context to be fact-checked.

#### Outputs
- reasoning (`str`): The detailed reasoning or rationale behind the evaluation.
- evaluation (`str`): The final evaluation of the fact-checking process. Possible values are `[factual]`, `[incorrect]`, or `[inconclusive]`.
- model (`str`): The model used for the task.

### Workflow Steps

1. Generate a search query based on the context and previous queries.
2. Perform a web search using the generated query.
3. Pick a URL from the search results.
4. Scrape the content from the selected URL.
5. Identify contradictions between the scraped content and the original context.
6. Evaluate the contradictions and provide a final assessment.

### Example

Perform a web-based fact-check on a given context. This example uses the default model.

```python
import os
import asyncio
from dria.factory import WebFactCheck
from dria.client import Dria
from dria.models import Task

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    web_fact_check = WebFactCheck()
    res = await dria.execute(
        Task(
            workflow=web_fact_check.workflow(context="The Earth is flat.").model_dump(),
        ),
        timeout=200,
    )
    return web_fact_check.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected result

```json
{
   "reasoning":"The AI assistant correctly identifies that it cannot confirm or deny the claim because the provided search results do not contain the specific GDP per capita figure for China in 2024.  \n\nTherefore, based solely on the information given, the evaluation must be: **[inconclusive]**. \n\n\n",
   "evaluation":"inconclusive",
   "model":"gemma2:9b-instruct-fp16"
}
```