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

Expected output

```json
{
  "input": "The flickering candlelight cast dancing shadows on the walls of the ancient library. Dust motes swirled in the faint breeze that wafted through the open window, carrying with it the scent of rain and decaying parchment. A lone raven perched atop a crumbling statue, its obsidian eyes gleaming in the dim light. The silence was broken only by the rustling of pages as I turned them, searching for answers within the countless volumes lining the shelves. Each book held a universe of knowledge, a whispered promise of forgotten lore and hidden truths. But tonight, my quest led me to a particularly worn volume, its leather cover cracked and faded. As I opened it, a musty odor filled the air, and a sense of unease settled over me. The script within was ancient and indecipherable, yet somehow, I felt drawn to its secrets.",
  "positive_document": "The aroma of freshly baked bread wafted through the cozy bakery, mingling with the sweet scent of cinnamon and vanilla. Sunlight streamed through the large windows, illuminating the display case filled with an assortment of pastries - croissants glistening with butter, muffins bursting with blueberries, and cakes adorned with delicate frosting. Behind the counter, a cheerful woman kneaded dough with practiced hands, her face etched with the satisfaction of creating something beautiful. The warmth of the oven radiated throughout the shop, inviting customers to linger over steaming cups of coffee and shared plates of warm treats. Laughter mingled with the clinking of mugs as friends caught up over their morning pastries, and the air buzzed with a sense of community and contentment. It was a haven of warmth and sweetness, a reminder that even in the midst of life's chaos, there is always room for simple pleasures.",
  "model": "gemma2:9b-instruct-fp16"
}
```