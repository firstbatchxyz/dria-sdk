from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from dria.models.enums import Model


class PipelineConfig(BaseModel):
    """
    Configuration settings for initializing and running a pipeline.

    Attributes:
        retry_interval (int): Time interval between retry attempts, in seconds.
        pipeline_timeout (int): Maximum allowed duration for the entire pipeline execution, in seconds.
    """
    retry_interval: int = Field(
        default=2,
        description="Time interval between retry attempts, in seconds",
        ge=0,
    )
    pipeline_timeout: int = Field(
        default=300,
        description="Maximum allowed duration for the entire pipeline execution, in seconds",
        ge=1,
    )

    @field_validator('retry_interval', 'pipeline_timeout')
    def validate_positive_values(cls, value, field):
        if value < 0:
            raise ValueError(f"{field.name} must be a non-negative integer")
        return value


DEFAULT_MODELS: List[Model] = [
    Model.GPT4_TURBO,
    Model.GPT4O,
    Model.O1_MINI,
    Model.O1_PREVIEW,
    Model.LLAMA3_1_8B_FP16,
    Model.GEMMA2_9B,
    Model.GEMMA2_9B_FP16,
    Model.QWEN2_5_7B_FP16,
    Model.QWEN2_5_32B_FP16
]


class StepConfig(BaseModel):
    """
    Configuration settings for an individual step within the pipeline.

    Attributes:
        models (List[Model]): List of AI models to be used in this step.
        min_compute (Optional[float]): Minimum required compute resources, expressed as a percentage (0.0 to 1.0).
        max_time (int): Maximum allowed duration for the step execution, in seconds.
        max_steps (int): Maximum number of sub-steps or iterations allowed within this step.
        max_tokens (int): Maximum number of tokens allowed to be processed in this step.
    """
    models: List[Model] = Field(
        default=DEFAULT_MODELS,
        description="List of AI models to be used in this step",
        min_items=1,
    )
    min_compute: Optional[float] = Field(
        default=1.0,
        description="Minimum required compute resources, expressed as a percentage (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    max_time: int = Field(
        default=200,
        description="Maximum allowed duration for the step execution, in seconds",
        ge=1,
    )
    max_steps: int = Field(
        default=20,
        description="Maximum number of sub-steps or iterations allowed within this step",
        ge=1,
    )
    max_tokens: int = Field(
        default=750,
        description="Maximum number of tokens allowed to be processed in this step",
        ge=1,
    )

    class Config:
        """
        Pydantic model configuration for StepConfig.

        Settings:
            allow_population_by_field_name (bool): Allows populating model fields by their names.
            validate_assignment (bool): Enables validation when assigning values to fields.
        """
        allow_population_by_field_name = True
        validate_assignment = True

    @field_validator('models')
    def validate_models(cls, models):
        if not isinstance(models, list):
            raise ValueError("The 'models' field must be a list of Model enum instances")
        if not all(isinstance(model, Model) for model in models):
            raise ValueError("All items in the 'models' field must be instances of the Model enum")
        return models
