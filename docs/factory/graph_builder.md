# GenerateGraph

`GenerateGraph` is a `SingletonTemplate` task that generates a graph of concepts and their relationships from a given context.

#### Inputs
- context (`str`): The context from which to extract the ontology of terms.

#### Outputs
- graph (`str`): A JSON-like string containing nodes and edges representing concepts and their relationships.
- model (`str`): The name of the model used for generation.

### Example

Generate a graph of concepts and their relationships based on a given context. This example uses the default model configured in the Dria client.

```python
import os
import asyncio
from dria.factory import GenerateGraph
from dria.models import Model
from dria.client import Dria
from dria.models import Task

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    generate_graph = GenerateGraph()
    context = "Artificial Intelligence is a broad field that includes machine learning and deep learning. Neural networks are a key component of deep learning systems."
    res = await dria.execute(
        Task(
            workflow=generate_graph.workflow(context=context).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=75,
    )
    return generate_graph.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "graph":[
      {
         "edge":"Machine learning is a subfield within the broader field of Artificial Intelligence.",
         "node_1":"Artificial Intelligence",
         "node_2":"machine learning"
      },
      {
         "edge":"Deep learning is another subfield of Artificial Intelligence that focuses on deep neural networks.",
         "node_1":"Artificial Intelligence",
         "node_2":"deep learning"
      },
      {
         "edge":"Deep learning is a specific approach within machine learning that uses deep neural networks to model complex patterns in data.",
         "node_1":"machine learning",
         "node_2":"deep learning"
      },
      {
         "edge":"Neural networks are crucial components used in the construction of deep learning systems.",
         "node_1":"neural networks",
         "node_2":"deep learning systems"
      }
   ],
   "model":"qwen2.5:32b-instruct-fp16"
}
```