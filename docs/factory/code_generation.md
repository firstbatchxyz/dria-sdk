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
- model (`str`): The model used for code generation.

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

Expected output

```json
{
   "instruction":"Write a function to calculate the factorial of a number",
   "language":"python",
   "code":"def factorial(n):\n    \"\"\"\n    Calculate the factorial of a non-negative integer n.\n    \n    Args:\n    n (int): A non-negative integer whose factorial is to be calculated.\n    \n    Returns:\n    int: The factorial of the input number.\n    \n    Raises:\n    ValueError: If n is negative.\n    \"\"\"\n    # Check if the input is a non-negative integer\n    if not isinstance(n, int) or n < 0:\n        raise ValueError(\"Input must be a non-negative integer.\")\n    \n    # Initialize the result to 1 (since 0! = 1)\n    result = 1\n    \n    # Calculate the factorial using a loop\n    for i in range(1, n + 1):\n        result *= i\n    \n    return result\n\n# Example usage:\ntry:\n    print(factorial(5))  # Output: 120\nexcept ValueError as e:\n    print(e)",
   "model":"qwen2.5-coder:1.5b"
}
```