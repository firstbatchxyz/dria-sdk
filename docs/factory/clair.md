# Clair

`Clair` is a `SingletonTemplate` task that takes a student solution and reasoning, and corrects the student solution.

#### Inputs
- task (`str`): The task description or problem statement.
- student_solution (`str`): The student's original solution to be corrected.

#### Outputs
- reasoning (`str`): The teacher's reasoning for the corrections.
- corrected_student_solution (`str`): The improved version of the student's solution.
- task (`str`): The original task description (echoed from input).
- student_solution (`str`): The original student solution (echoed from input).

### Example

Generate a corrected student solution based on a given task and the student's original solution. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import Clair
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    clair = Clair()
    task = "Write a function to calculate the factorial of a number."
    student_solution = "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)"
    
    res = await dria.execute(
        Task(
            workflow=clair.workflow(task=task, student_solution=student_solution).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=45,
    )
    return clair.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print("Teacher's Reasoning:")
    print(result["reasoning"])
    print("\nCorrected Student Solution:")
    print(result["corrected_student_solution"])

if __name__ == "__main__":
    main()
```
