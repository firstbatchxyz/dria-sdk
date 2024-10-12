# SemanticTriplet

`SemanticTriplet` is a `Singleton` task that generates a JSON object containing three textual units with specified semantic similarity scores.

#### Inputs
- unit (`str`): The type of textual unit to generate (e.g., "sentence", "paragraph").
- language (`str`): The language in which the units should be written.
- high_score (`int`): The similarity score between S1 and S2 (1 to 5).
- low_score (`int`): The similarity score between S1 and S3 (1 to 5).
- difficulty (`str`): The education level required to understand the units (e.g., "college", "high school").

#### Outputs
- semantic_triple (`dict`): A JSON object containing three textual units (S1, S2, S3) with specified semantic similarity scores.

### Example

Generate a semantic triplet with specified parameters. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import SemanticTriplet
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    semantic_triplet = SemanticTriplet()
    res = await dria.execute(
        Task(
            workflow=semantic_triplet.workflow(
                unit="sentence",
                language="English",
                high_score=4,
                low_score=2,
                difficulty="college"
            ).model_dump(),
            models=[Model.LLAMA3_2_3B],
        ),
        timeout=45,
    )
    return semantic_triplet.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
```

Expected output

```json
{
  "S1": "The intricate dance of quantum fluctuations within the cosmos is a fascinating phenomenon that has garnered significant attention from physicists.",
  "S2": "The dynamic interplay between chaos theory and cosmology reveals a profound understanding of the universe's underlying mechanisms.",
  "S3": "In the realm of relativity, the curvature of spacetime is a fundamental concept that underpins our comprehension of the cosmos.",
  "model": "llama3.2:3b"
}
```