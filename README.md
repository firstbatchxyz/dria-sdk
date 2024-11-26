# Dria-SDK

Dria SDK is a powerful SDK for building and executing AI-powered workflows and pipelines. It provides a flexible and extensible framework for creating complex AI tasks, managing distributed computing resources, and handling various AI models.

## Table of Contents

1. [Installation](#installation)
2. [Features](#features)
3. [Login](#login)
4. [Getting Started](#getting-started)
5. [Usage Examples](#usage-examples)
6. [API Usage](#api-usage)
7. [License](#license)

## Installation

To install Dria SDK, you can use pip:

```bash
pip install dria
```

## Features

- Create and manage AI workflows and pipelines
- Support for multiple AI models
- Distributed task execution
- Flexible configuration options
- Built-in error handling and retries
- Extensible callback system

## Login


Community Network

Dria Community Network consists of community nodes with LLMs and tool usage capabilities. Visit the [Dria Login API](https://dkn.dria.co/auth/generate-token) and get your unique RPC token.

Pro Network

Dria Pro Network consists of high performance nodes, equipped with even more powerful LLMs, compute and 99.9% reliability. Pro Network is more suitable for production-grade applications and partners in the ecosystem. Please fill out the [form](https://forms.gle/yGtLZw3HPW7kgD427) to get access to the Pro Network

## Getting Started

```python
import os
from dria.client import Dria

# Initialize the Dria client
dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

```



## Usage Examples

### Creating a Simple Workflow

Here's an example of creating a simple workflow for generating a poem:

```python
import os
import asyncio
from dria.factory import Simple
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    simple = Simple()
    res = await dria.execute(
        Task(
            workflow=simple.workflow(prompt="Write a poem about love"),
            models=[Model.GPT4O],
        ),
        timeout=45,
    )
    return simple.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)
```

### Building a Complex Pipeline

For more complex scenarios, you can use the `PipelineBuilder` to create multi-step pipelines:

Here's an example of a pipeline that extends a list.

```python
import logging
from typing import Optional, List, Union

from dria.client import Dria
from dria.models import Model
from dria.pipelines import Pipeline
from dria.pipelines.builder import PipelineBuilder
from .extender import ListExtender
from .generate_subtopics import GenerateSubtopics

logger = logging.getLogger(__name__)


class ListExtenderPipeline:

    def __init__(
            self,
            dria: Dria,
            models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = models or [
            [Model.GEMMA2_9B_FP16],
            [Model.GPT4O],
        ]

    def build(self, list: List[str], granularize: bool = False) -> Pipeline:
        self.pipeline.input(e_list=list)
        self.pipeline << ListExtender().set_models(self.models_list[0]).custom()
        if granularize:
            (
                    self.pipeline
                    << GenerateSubtopics().set_models(self.models_list[1]).custom()
            )
        return self.pipeline.build()


```

### API Usage

You can use the Dria SDK on the API level to create your own workflows and pipelines.

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from dria.client import Dria
from pipeline import create_subtopic_pipeline

app = FastAPI(title="Dria SDK Example")
dria = Dria()


@app.on_event("startup")
async def startup_event():
    await dria.initialize()


class PipelineRequest(BaseModel):
    input_text: str = Field(..., description="The input text for the pipelines to process")


class PipelineResponse(BaseModel):
    pipeline_id: str = Field(..., description="Unique identifier for the created pipelines")


pipelines = {}


@app.post("/run_pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    pipeline = await create_subtopic_pipeline(dria, request.input_text)
    pipelines[pipeline.pipeline_id] = pipeline
    background_tasks.add_task(pipeline.execute)
    return PipelineResponse(pipeline_id=pipeline.pipeline_id)


@app.get("/pipeline_status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    if pipeline_id not in pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = pipelines[pipeline_id]
    state, status, result = pipeline.poll()

    if result is not None:
        del pipelines[pipeline_id]

    return {"status": status, "state": state, "result": result}

# Usage example:
# uvicorn main:app --host 0.0.0.0 --port 8005

```

For more detailed API documentation, see on our [documentation site](https://docs.dria.co).

## License

Dria SDK is released under the [MIT License](https://opensource.org/licenses/MIT).
