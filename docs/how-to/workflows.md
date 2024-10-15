# Workflows

Workflows are the instruction sets within a `Task`, allowing Dria nodes to breakdown complex tasks into smaller tasks.
There maybe cases Singletons and Pipelines won't cover all the requirements of a task, in such cases, custom workflows come in handy.
Dria SDK provides a way to create workflows through `dria_workflows` package. 

<img src="how-to/diagram_2.png" alt="Workflow Diagram" width=70%/>

A workflow consists of steps that interact with LLMs and I/O memory. 
Each step reads inputs from memory, generates text, and writes outputs back to memory. 
Workflows enable inter-step communication via [memory](#memory-operations).

## Creating a Workflow

Workflows define the execution flow of tasks involving Large Language Models (LLMs). 
By using the dria_workflows Python package, you can construct these workflows more efficiently. 

Key components of a `Workflow`:
- Configuration (config): An object containing settings like maximum steps, time limits, and tools.
- Steps: A list of steps defining the individual units of work in the workflow.
- Flow: A list specifying the execution order and conditional logic between tasks.
- Return Value: A memory key indicating what value to return at the end of the workflow.

In Dria, you create a `WorkflowBuilder` instance to start building your workflow:

```python
from dria_workflows import WorkflowBuilder
builder = WorkflowBuilder()
```

The configuration settings control the workflow’s execution parameters. 
You can set them using methods on the WorkflowBuilder instance.

`max_steps`: The maximum number of steps the workflow can execute.

`max_time`: The maximum time (in seconds) the workflow can run.

`max_tokens`: The maximum number of tokens the LLM can generate.

These are limitations to prevent infinite loops or excessive resource usage. You can set them as follows:

```python
builder.set_max_steps(5)
builder.set_max_time(100)
builder.set_max_tokens(750)
```

Dria nodes provides several built-in [tools](#step-a-random-variable-generation) that is included in your workflow by default.
Tools include:
- Search: Tools for searching and retrieving data.
- Scrape: Tools for scraping data from the web.
- Stock: Tool for retrieving stock data.


#### Steps

Each step describes a task in the workflow.
Here is a simple workflow with a single step:

```python
from dria_workflows import WorkflowBuilder, Operator, Write
builder = WorkflowBuilder()
builder.generative_step(
    id="task_id",
    prompt="What is 2+2?",
    operator=Operator.GENERATION,
    outputs=[Write.new("result")],
)
```

Let's break down the workflow step:

- Create a step named `task_id`
- Use the prompt "What is 2+2?" as your instruction
- Set the operator to `Operator.GENERATION` for text generation
- Define the output to write the result to the memory key `result`

[*Memory*](#memory-operations) is a crucial component of workflows. It allows inter-step data transfer. 

#### *Step types*

There are two types of steps in a workflow:

`generative_step()` -> Steps that generate text using an LLM.
- operator `Operator`
  - GENERATION: Generates text using an LLM.
  - FUNCTION_CALLING: Used for calling built-in functions. Will execute the function and return the result.
  - FUNCTION_CALLING_RAW: Used for calling built-in or custom functions. Will return a function call without executing it.
- prompt `str`: The prompt for the LLM.
- path `str`: The path to a markdown file containing the prompt.
- id `str`: The unique ID for the step.


`search_step()`: Steps that perform a [search](#step-b-validation) operation through the file system.
- search_query `str`: The query to search for.
- id `str`: The unique ID for the step.

> Search is a built-in functionality of Dria nodes. Each node has a file system (vectorDB) that stores data for semantic search. Searchable data is inserted through `Insert` [output](#memory-operations) type.

# Memory Operations

Memory operations allow tasks to read from and write to different storage mechanisms: cache, stack, and file system.
Cache is a *KV cache*. Stack is a *LIFO stack*. File system is a *vectorDB* for semantic search.

#### Inputs

Before interacting with LLM, steps read inputs from memory and replace variables written `{{history}}` in prompts with actual values.
It serves as a template engine like [jinja](https://github.com/pallets/jinja).

- Read: Reads a value from the cache.
- Pop: Pops the last value from a stack.
- Peek: Peeks at a value (with index) in a stack.
- GetAll: Retrieves all values from a stack.
- Search: Performs a semantic search in the file system.

Code examples

```python
from dria_workflows import Read, GetAll, Peek, Pop, Search
inputs=[
    Read.new(key="user_input", required=True),
    GetAll.new(key="history", required=False),
    Peek.new(key="last_input", index=0, required=False),
    Pop.new(key="last_output", required=False),
    Search.new(query="search_query", required=True),
]
```

`required` field in inputs specifies if the input is mandatory for the task, forcing executor to halt if not found. 

#### Outputs

After step is executed, results are written back to memory for future steps to use.

- Write: Writes a value to the cache.
- Push: Pushes a value onto a stack.
- Insert: Inserts a value into the file system.

Code Example
```python
from dria_workflows import Write, Push, Insert
outputs=[
    Write.new(key="processed_input"),
    Push.new(key="input_history"),
    Insert.new(key="search_query"),
]
```

# Flows

Steps define the execution flow between tasks, including conditional logic.
Use the flow method to set up the steps:

```python
from dria_workflows import Edge
flow = [
    Edge(source="task_a", target="task_b"),
    Edge(source="task_b", target="_end"),
]
builder.flow(flow)
```


- source: The ID of the source task.
- target: The ID of the target task.
- fallback (optional): The ID of the task to jump to if the condition is not met.
- condition (optional): A condition to evaluate before moving to the target task.
- _end: A special task ID indicating the end of the workflow.

#### Conditions

You can add conditions to steps to control the flow based on certain criteria.
*Defining a Condition*

```python
from dria_workflows import ConditionBuilder, Read, Expression
condition=ConditionBuilder.build(
    input=Read.new(key="validation_result", required=True),
    expression=Expression.EQUAL,
    expected="Yes",
    target_if_not="task_a",
)
```

- input: The input to evaluate.
- expression: The comparison operator (e.g., Expression.EQUAL).
- expected: The expected value to compare against.
- target_if_not: The task to jump to if the condition is not met.

Example with Condition

```python
from dria_workflows import Edge, ConditionBuilder, Read, Expression
Edge(
    source="validate_data",
    target="_end",
    condition=ConditionBuilder.build(
        input=Read.new(key="is_valid", required=True),
        expression=Expression.EQUAL,
        expected="True",
        target_if_not="data_generation",
    ),
),
```



Example Workflow

Below is a complete example of creating a workflow using dria_workflows.

Workflow Description

We will create a workflow that:

	1.	Generates random variables based on a simulation description.
	2.	Validates the generated variables.
	3.	If validation fails, it regenerates the variables.

Step-by-Step Implementation

1. Initialize the Workflow Builder

```python
from dria_workflows import WorkflowBuilder
simulation_description = "Describe your simulation here."
builder = WorkflowBuilder(simulation_description=simulation_description)
builder.set_max_time(90)
builder.set_max_tokens(750)
```
2. Define the First Task: Random Variable Generation

```python
from dria_workflows import Operator, Read, Write
builder.generative_step(
    id="random_var_gen",
    path="path/to/prompt.md",
    operator=Operator.GENERATION,
    inputs=[
        Read.new(key="simulation_description", required=True),
        Read.new(key="is_valid", required=False),
    ],
    outputs=[Write.new(key="random_vars")],
)
```

Inputs:
- Reads simulation_description.
- Optionally reads is_valid (useful if looping back after a failed validation).
- Outputs:
- Writes the generated variables to random_vars.

3. Define the Second Task: Validation

```python
from dria_workflows import Operator, Read, Write
builder.generative_step(
    id="validate_random_vars",
    path="path/to/validate.md",
    operator=Operator.GENERATION,
    inputs=[
        Read.new(key="simulation_description", required=True),
        Read.new(key="random_vars", required=True),
    ],
    outputs=[Write.new(key="is_valid")],
)
```

Inputs:
- Reads simulation_description.
- Reads the generated random_vars.
Outputs:
- Writes the validation result to is_valid.

4. Define the Workflow Steps

```python
flow = [
    Edge(source="random_var_gen", target="validate_random_vars"),
    Edge(
        source="validate_random_vars",
        target="_end",
        condition=ConditionBuilder.build(
            input=Read.new(key="is_valid", required=True),
            expression=Expression.EQUAL,
            expected="Yes",
            target_if_not="random_var_gen",
        ),
    ),
]
builder.flow(flow)
```

First Edge: From random_var_gen to validate_random_vars.
Second Edge: From validate_random_vars to _end or back to random_var_gen based on the validation result.

5. Set the Return Value

```python
builder.set_return_value("random_vars")
```

