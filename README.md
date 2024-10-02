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

Dria SDK uses authentication token for sending tasks to the Dria Network. You should get your rpc token from [Dria Login API](https://dkn.dria.co/auth/generate-token).

## Getting Started

To get started with Dria SDK, you'll need to set up your environment and initialize the Dria client:

```python
import os
from dria.client import Dria

# Initialize the Dria client
dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

# Initialize the client (should be called before using any other methods)
await dria.initialize()
```



## Usage Examples

### Creating a Simple Workflow

Here's an example of creating a simple workflow for generating a poem:

```python
import asyncio

from dria.client import Dria
from dria.models import Task, TaskResult
from dria.models.enums import Model
from dria.workflows.lib.poem_generator import poem

dria = Dria()

async def generate_poem(prompt: str) -> list[TaskResult]:
    task = Task(
        workflow=poem(prompt),
        models=[Model.QWEN2_5_7B_FP16]
    )
    await dria.push(task)
    return await dria.fetch(task_id=task.id)

async def main():
    
    await dria.initialize()
    result = await generate_poem("Write a poem about love")

if __name__ == "__main__":
    asyncio.run(main())
```

### Building a Complex Pipeline

For more complex scenarios, you can use the `PipelineBuilder` to create multi-step pipelines:

```python
from dria.client import Dria
from dria.models import Model, TaskInput
from dria.pipelines import PipelineConfig, StepConfig, PipelineBuilder, StepBuilder
from workflows import generate_entries, generate_subtopics


async def create_subtopic_pipeline(dria: Dria, topic, config: PipelineConfig = PipelineConfig(), max_depth=1):
    pipeline = PipelineBuilder(config, dria)
    depth = 0

    # handles single topic output
    subtopics = StepBuilder(input=TaskInput(topics=[topic]), config=StepConfig(models=[Model.QWEN2_5_7B_FP16,
                                                                                       Model.GPT4O]),
                            workflow=generate_subtopics).broadcast().build()
    pipeline.add_step(subtopics)

    while depth < max_depth:
        # handles multiple topics
        subtopics = StepBuilder(workflow=generate_subtopics,
                                config=StepConfig(models=[Model.QWEN2_5_7B_FP16, Model.GPT4O])).scatter().build()
        pipeline.add_step(subtopics)
        depth += 1

    # entry generation
    entries = StepBuilder(workflow=generate_entries, config=StepConfig(min_compute=0.8)).build()
    pipeline.add_step(entries)
    return pipeline.build()

```

### API Usage

You can use the Dria SDK on the API level to create your own workflows and pipelines.

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from dria.client import Dria
from dria.pipelines.pipeline import PipelineConfig, Pipeline
from pipeline import create_subtopic_pipeline

app = FastAPI(title="Dria SDK Example")
dria = Dria()

@app.on_event("startup")
async def startup_event():
    await dria.initialize()

class PipelineRequest(BaseModel):
    input_text: str = Field(..., description="The input text for the pipeline to process")

class PipelineResponse(BaseModel):
    pipeline_id: str = Field(..., description="Unique identifier for the created pipeline")

pipeline_config = PipelineConfig(retry_interval=5)
pipelines = {}

@app.post("/run_pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    pipeline = await create_subtopic_pipeline(dria, request.input_text, pipeline_config)
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

For more detailed API documentation, see on our [documentation site](https://docs.dria.ai).

## License

Dria SDK is released under the [MIT License](https://opensource.org/licenses/MIT).
