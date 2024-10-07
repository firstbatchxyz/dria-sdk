import asyncio
import logging
import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from dria.client import Dria
from dria.pipelines.pipeline import PipelineConfig, Pipeline
from pipeline import create_subtopic_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dria SDK Example")
dria = Dria()


# Initialize the Dria client
@app.on_event("startup")
async def startup_event():
    await dria.initialize()


class PipelineRequest(BaseModel):
    input_text: str = Field(
        ..., description="The input text for the pipeline to process"
    )


class PipelineResponse(BaseModel):
    pipeline_id: str = Field(
        ..., description="Unique identifier for the created pipeline"
    )


class PipelineStatus(BaseModel):
    status: str = Field(..., description="Current status of the pipeline")
    state: str = Field(None, description="Current state of the pipeline if running")
    result: Dict[str, Any] = Field(
        None, description="Result of the pipeline if completed"
    )


# Create a pipeline configuration
pipeline_config = PipelineConfig(retry_interval=5)

pipelines: Dict[str, Pipeline] = {}


@app.post("/run_pipeline", response_model=PipelineResponse, status_code=202)
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    try:
        pipeline = await create_subtopic_pipeline(
            dria, request.input_text, pipeline_config
        )
        pipelines[pipeline.pipeline_id] = pipeline
        background_tasks.add_task(pipeline.execute)
        logger.info(f"Pipeline {pipeline.pipeline_id} created and started")
        return PipelineResponse(pipeline_id=pipeline.pipeline_id)
    except Exception as e:
        logger.error(f"Error creating pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/pipeline_status/{pipeline_id}", response_model=PipelineStatus)
async def get_pipeline_status(pipeline_id: str):
    if pipeline_id not in pipelines:
        logger.warning(f"Pipeline {pipeline_id} not found")
        raise HTTPException(status_code=404, detail="Pipeline not found")

    try:
        pipeline = pipelines[pipeline_id]
        state, status, result = pipeline.poll()

        if result is None:
            return PipelineStatus(status=status, state=state)
        else:
            del pipelines[pipeline_id]
            return PipelineStatus(status=status, result=result)
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
