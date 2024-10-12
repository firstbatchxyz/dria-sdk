# TextRetrieval

`TextRetrieval` is a `Singleton` task that generates a JSON object containing a user query, a positive document, and a hard negative document for a specified text retrieval task.

#### Inputs
- task_description (`str`): The description of the retrieval task.
- query_type (`str`): The type of the user query (e.g., "informational", "navigational").
- query_length (`str`): The length of the user query (e.g., "short", "long").
- clarity (`str`): The clarity of the user query (e.g., "clear", "ambiguous").
- num_words (`int`): The minimum number of words for the documents.
- language (`str`): The language in which the query and documents should be written.
- difficulty (`str`): The education level required to understand the query and documents (e.g., "college", "high school").

#### Outputs
- JSON object containing:
  - user_query (`str`): A random user search query specified by the retrieval task.
  - positive_document (`str`): A relevant document for the user query.
  - hard_negative_document (`str`): A hard negative document that only appears relevant to the query.
  - model (`str`): The model used for generation.

### Example

Generate a text retrieval example based on the specified parameters. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import TextRetrieval
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    text_retrieval = TextRetrieval()
    res = await dria.execute(
        Task(
            workflow=text_retrieval.workflow(
                task_description="Generate a text retrieval example for a science topic",
                query_type="informational",
                query_length="short",
                clarity="clear",
                num_words=100,
                language="English",
                difficulty="high school"
            ).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return text_retrieval.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "user_query":"Effects of Climate Change on Polar Bears",
   "positive_document":"Polar bears are one of the most iconic and majestic creatures in the Arctic ecosystem. However, their populations have been declining over the past few decades due to various reasons, including habitat loss and hunting. The primary threat to polar bears is the melting of sea ice caused by climate change. As a result, they struggle to hunt for seals, their primary source of food, which are found in and around sea ice.According to a study published in the journal Nature Climate Change, the Arctic has been warming at a rate twice as fast as the global average over the past 30 years. This rapid warming has led to significant changes in polar bear behavior and ecology. For instance, they have started spending more time on land than on sea ice, which affects their ability to hunt and feed.The consequences of climate change on polar bears are far-reaching and severe. They may eventually lose their primary source of food, leading to malnutrition, starvation, and even death. Moreover, the loss of sea ice will also affect other marine species that rely on it for survival, including walruses, seals, and belugas.To mitigate these effects, scientists recommend reducing greenhouse gas emissions, conserving energy, and implementing policies to protect polar bear habitats. Governments and organizations worldwide are working together to address this pressing issue and ensure the long-term survival of polar bears in a rapidly changing climate.",
   "hard_negative_document":"Climate change is a global phenomenon that affects various ecosystems around the world. While it has significant impacts on marine life, including coral bleaching and ocean acidification, its effects on terrestrial ecosystems are often overlooked. However, research suggests that climate change can lead to changes in vegetation patterns, altered fire regimes, and shifts in animal migration routes.For example, some studies have shown that warming temperatures in the Amazon rainforest have led to an increase in wildfires, which can release massive amounts of carbon dioxide into the atmosphere. Additionally, climate-driven changes in precipitation patterns have affected agricultural productivity, leading to food shortages in some regions.While climate change is a pressing concern for polar bears, its effects on terrestrial ecosystems are equally significant and warrant further research. By studying these impacts, we may gain valuable insights into the complex relationships between climate change, biodiversity, and ecosystem resilience.",
   "model":"llama3.1:8b-instruct-fp16"
}
```