# TextClassification

`TextClassification` is a `Singleton` task that generates a JSON object containing an example for a text classification task.

#### Inputs
- task_description (`str`): The description of the text classification task.
- language (`str`): The language in which the texts should be written.
- clarity (`str`): The clarity of the input text (e.g., "clear", "ambiguous").
- difficulty (`str`): The education level required to understand the input text (e.g., "college", "high school").

#### Outputs
- classification_example (`dict`): A JSON object containing 'input_text', 'label', and 'misleading_label' for the specified text classification task.

### Example

Generate a text classification example based on the given parameters. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
import json
from dria.factory import TextClassification
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    text_classification = TextClassification()
    res = await dria.execute(
        Task(
            workflow=text_classification.workflow(
                task_description="Classify movie reviews as positive or negative",
                language="English",
                clarity="clear",
                difficulty="high school"
            ).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return text_classification.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

Expected output

```json
{
  "input_text": "The plot was somewhat predictable, but the performances were top-notch and kept me engaged throughout.",
  "label": "positive",
  "misleading_label": "negative",
  "model": "qwen2.5:32b-instruct-fp16"
}
```

#### References

- [Distilabel TextClassification](https://distilabel.argilla.io/latest/components-gallery/tasks/textclassification/)
- [Improving Text Embeddings with Large Language Models](https://arxiv.org/abs/2401.00368)