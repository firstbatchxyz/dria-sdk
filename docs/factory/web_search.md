# WebSearch

`WebSearch` is a `SingletonTemplate` task that performs web searches and evaluations to answer multiple-choice questions.

#### Inputs
- topic (`str`): The topic to search for.
- mode (`Mode`): The search mode, either "WIDE" or "NARROW".

#### Outputs
- notes (`List[str]`): A list of summarized notes from the web search.
- model (`str`): The model used for the task.

### Example

Perform a web search on a given topic. This example uses the "WIDE" mode.

```python
import os
import asyncio
from dria.factory import WebSearch
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    web_search = WebSearch()
    res = await dria.execute(
        Task(
            workflow=web_search.workflow(topic="Solomonoff Induction", mode="NARROW").model_dump(),
            models=[Model.LLAMA3_1_8B_FP16],
        ),
        timeout=200,
    )
    return web_search.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "notes":[
      "The discussion revolves around Solomonoff induction, a concept that involves using probability theory to make predictions about future events based on past data. Some users express skepticism and criticism towards the idea, arguing that it is impractical, incomputable, and not useful for measuring the relative complexity of different theories. One user suggests rebranding it as \\\"Solomonoff\\'s EDM\\\" or \\\"Solomonoff\\'s EUV process\\\". Another user defends Solomonoff induction by comparing it to Occam\\'s razor, which has been a guiding principle in science without being proven."
   ],
   "model":"llama3.1:8b-instruct-fp16"
}
```