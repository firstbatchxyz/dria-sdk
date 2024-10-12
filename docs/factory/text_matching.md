# TextMatching

`TextMatching` is a `Singleton` task that generates a JSON object with 'input' and 'positive_document' for a specified text matching task.

#### Inputs
- task_description (`str`): The description of the text matching task.
- language (`str`): The language in which the texts should be written.

#### Outputs
- text_matching_example (`dict`): A JSON string containing the generated 'input' and 'positive_document'.

### Example

Generate a text matching example based on task description and language. This example uses `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
import json
from dria.factory import TextMatching
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    text_matching = TextMatching()
    res = await dria.execute(
        Task(
            workflow=text_matching.workflow(
                task_description="Generate a text matching example for sentiment analysis",
                language="English"
            ).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return text_matching.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

```