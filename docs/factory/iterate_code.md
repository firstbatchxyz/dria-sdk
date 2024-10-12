# IterateCode

`IterateCode` is a `Singleton` task that iterates and improves existing code based on given instructions.

#### Inputs
- code (`str`): The original code to iterate over.
- instruction (`str`): The instruction to guide code generation.
- language (`Language`): The programming language to generate code for.

#### Outputs
- instruction (`str`): The original instruction.
- language (`Language`): The programming language used.
- iterated_code (`str`): The improved and iterated code.
- code (`str`): The original input code.
- model (`str`): The model used for code generation.

### Example

Iterate and improve existing code based on instructions. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import IterateCode
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    iterate_code = IterateCode()
    original_code = """
    def greet(name):
        print("Hello, " + name)
    """
    instruction = "Add error handling for empty name input"
    
    res = await dria.execute(
        Task(
            workflow=iterate_code.workflow(code=original_code, instruction=instruction, language="python").model_dump(),
            models=[Model.DEEPSEEK_CODER_6_7B],
        ),
        timeout=45,
    )
    return iterate_code.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "instruction":"Add error handling for empty name input",
   "language":"python",
   "iterated_code":"def greet(name):\n    # Check if the input is not None and strip leading/trailing whitespace characters\n    if name and name.strip():\n        print(\"Hello, \" + name)\n    else:\n        raise ValueError(\\'Name cannot be empty\\')  # Raise an error if the name is empty or contains only spaces",
   "code":"\n    def greet(name):\n        print(\"Hello, \" + name)\n    ",
   "model":"deepseek-coder:6.7b"
}
```