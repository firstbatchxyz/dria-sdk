# GenerateCode

`GenerateCode` is a `SingletonTemplate` task that generates code based on an instruction and specified programming language.

> ⚠️ `GenerateCode` works best with coder models. You can use them with `Model.CODER`or specifying with `Model.QWEN2_5_CODER_1_5B`.

#### Inputs
- instruction (`str`): The instruction to generate code for.
- language (`Language`): The programming language to generate code in.

#### Outputs
- instruction (`str`): The original instruction.
- language (`Language`): The specified programming language.
- code (`str`): The generated code.

### Example

Generate Python code based on an instruction. This example uses the `QWEN2_5_CODER_1_5B` model.

```python
import os
import asyncio
from dria.factory import GenerateCode
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    generate_code = GenerateCode()
    res = await dria.execute(
        Task(
            workflow=generate_code.workflow(
                instruction="Write a function to calculate the factorial of a number",
                language="python"
            ).model_dump(),
            models=[Model.QWEN2_5_CODER_1_5B],
        ),
        timeout=45,
    )
    return generate_code.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```


```bash
{
   "instruction":"Write a function to calculate the factorial of a number",
   "language":"python",
   "code":"def factorial(n):\n    \"\"\"\n    Calculate the factorial of a non-negative integer n.\n    \n    Args:\n    n (int): A non-negative integer whose factorial is to be calculated.\n    \n    Returns:\n    int: The factorial of n.\n    \"\"\"\n    # Check if the input is a non-negative integer\n    if not isinstance(n, int) or n < 0:\n        raise ValueError(\"Input must be a non-negative integer.\")\n    \n    # Base case: factorial of 0 or 1 is 1\n    if n == 0 or n == 1:\n        return 1\n    \n    # Recursive case: n * factorial of (n-1)\n    else:\n        return n * factorial(n - 1)\n\n# Example usage\nprint(factorial(5))  # Output: 120"
}
```