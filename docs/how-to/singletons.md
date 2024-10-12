# Singletons

Singletons are a set of pre-built tasks that are designed to perform specific functions. 
They are called singletons because they are designed to be used as single instances that perform a specific task. 
Singletons are a powerful tool that can be used to quickly and easily perform a wide range of tasks without having to write custom code.

In order to use a singleton, you simply need to import the singleton class and create a `Task` instance with it.
Here is an example of how to use a singleton to perform a simple task:

Import the singleton class

```python
from dria.factory import EvolveInstruct
```

Create an instance of `Task` using the singleton

```python
evolve_instruct = EvolveInstruct()
original_prompt = "Explain the concept of photosynthesis."
task = Task(
    workflow=evolve_instruct.workflow(prompt=original_prompt, mutation_type="DEEPEN").model_dump(),
    models=[Model.GEMMA2_9B_FP16],
)
```

Each `Singleton` has two abstract methods:

1. `workflow`: This method returns the workflow that the singleton will execute. The workflow is a series of steps that the singleton will perform in order to complete its task.
2. `parse_result`: This method takes the result of the task and parses it into a human-readable format.

Find all available [singletons](factory/simple.md) in the `dria.factory` module.




