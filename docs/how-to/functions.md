# Functions

Dria Nodes provides several built-in tools that are included in your workflow by default. 
Selecting `Operator.FUNCTION_CALLING` will pick a tool from the list of built-in tools and execute it based on the instruction provided.

Example Step:

```python
builder.generative_step(
    id="task_id",
    prompt="What are the current prices of $AAPL and $GOOGL?",
    operator=Operator.FUNCTION_CALLING,
    outputs=[Write.new("result")]
)
```

Step above will select the `Stock` tool and execute it based on the instruction provided.

See [workflows](how-to/workflows.md) for available built-in tools.

# Custom Functions

Dria enables you to create custom functions (tools) that can be used in your workflows. 
These functions can be used to perform custom operations that are not natively supported by Dria.

Dria supports two types of custom functions:

- `CustomTool`: A pydantic model that can be used in your workflows.

`CustomTool` will not be executed by Dria. Instead, it will be returned as a function call in the workflow output.

- `HttpRequestTool`: An HTTP request tool that can be used to make HTTP requests in your workflows. 

`HttpRequestTool` will be executed by Dria and the result will be returned in the workflow output.

#### CustomTool

To create a custom function, you need to create a class that inherits from `CustomTool` and implement the `execute` method.

```python
from dria_workflows import CustomTool
from pydantic import Field

class SumTool(CustomTool):
    name: str = "calculator"
    description: str = "A tool sums integers"
    lhs: int = Field(0, description="Left hand side of sum")
    rhs: int = Field(0, description="Right hand side of sum")

    def execute(self, **kwargs):
        return self.lhs + self.rhs
```

`name` and `description` are required fields that describe the custom function. 
For the rest of your custom function, you can define any number of fields that you need.
If field has a default value, it means it's a required field.

To incorporate the custom function into your workflow, simple call `add_custom_tool` method on the `WorkflowBuilder` instance.

```python
builder = WorkflowBuilder()
builder.add_custom_tool(SumTool())
```

This would add the custom function to the list of available functions in your workflow.

```python
builder.generative_step(
    id="sum",
    prompt=f"What is {lhs} + {rhs}?",
    operator=Operator.FUNCTION_CALLING_RAW,
    outputs=[Write.new("call")]
)
```

Steps that incorporate custom functions should use `Operator.FUNCTION_CALLING_RAW` as the operator. 
This would force Dria Nodes to return the function call without executing it.

Below is a full example of a workflow that sums two numbers using a custom function:

```python
import asyncio
import logging
import os

from dotenv import load_dotenv
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, CustomTool
from pydantic import Field

from dria.client import Dria
from dria.models import Task, Model

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Dria client
dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


class SumTool(CustomTool):
    name: str = "calculator"
    description: str = "A tool sums integers"
    lhs: int = Field(0, description="Left hand side of sum")
    rhs: int = Field(0, description="Right hand side of sum")

    def execute(self, **kwargs):
        return self.lhs + self.rhs


def workflow(lhs: int, rhs: int):
    """
    Create a workflow to sum two numbers
    :param lhs:
    :param rhs:
    :return:
    """

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    builder = WorkflowBuilder()
    builder.add_custom_tool(SumTool())

    builder.generative_step(
        id="sum",
        prompt=f"What is {lhs} + {rhs}?",
        operator=Operator.FUNCTION_CALLING_RAW,
        outputs=[Write.new("call")]
    )

    flow = [
        Edge(source="sum", target="_end")
    ]
    builder.flow(flow)
    builder.set_return_value("call")
    return builder.build_to_dict()


async def main():
    lhs, rhs = 10932, 20934

    await dria.initialize()
    results = await dria.execute(Task(
        workflow=workflow(lhs, rhs),
        models=[
            Model.QWEN2_5_7B_FP16,
            Model.GPT4O
        ]
    ))

    for result in results:
        for call in result.parse():
            print(call.execute([SumTool]))


if __name__ == "__main__":
    asyncio.run(main())
```

#### HttpRequestTool

`HttpRequestTool` is a tool that can be used to make HTTP requests in your workflows. 
Unlike `CustomTool`, `HttpRequestTool` will be executed by Dria Nodes and the result will be returned in the workflow output.

To create an `HttpRequestTool`, you need to create a class that inherits from `HttpRequestTool` and implement the `execute` method.

```python
from dria_workflows import HttpRequestTool, HttpMethod
class PriceFeedTool(HttpRequestTool):
    name: str = "PriceFeedRequest"
    description: str = "Fetches price feed from Gemini API"
    url: str = "https://api.gemini.com/v1/pricefeed"
    method: HttpMethod = HttpMethod.GET
```

An `HttpRequestTool` requires the following fields:

- `name`: The name of the tool.
- `description`: A description of the tool.
- `url`: The URL to make the HTTP request to.
- `method`: The HTTP method to use for the request.
- `headers`: Optional headers to include in the request.
- `body`: Optional body to include in the request.

A `HttpRequestTool` can be added to the workflow in the same way as a `CustomTool`. 
Here is an example of a workflow that fetches cryptocurrency prices using an `HttpRequestTool`:

```python
class PriceFeedTool(HttpRequestTool):
    name: str = "PriceFeedRequest"
    description: str = "Fetches price feed from Gemini API"
    url: str = "https://api.gemini.com/v1/pricefeed"
    method: HttpMethod = HttpMethod.GET


def workflow():
    """
    Create a workflow to get cryptocurrency prices
    :return:
    """

    builder = WorkflowBuilder()
    builder.add_custom_tool(PriceFeedTool())

    builder.generative_step(
        id="get_prices",
        prompt=f"What is the BTC/USDT parity?",
        operator=Operator.FUNCTION_CALLING,
        outputs=[Write.new("prices")]
    )

    flow = [
        Edge(source="get_prices", target="_end")
    ]
    builder.flow(flow)
    builder.set_return_value("prices")
    return builder.build()
```