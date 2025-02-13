from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """Configuration parameters for workflow execution"""

    max_tokens: int = Field(
        default=1000,
        description="Maximum number of tokens allowed for generation steps",
    )
    max_steps: int = Field(
        default=10, description="Maximum number of steps allowed in workflow execution"
    )
    max_time: int = Field(
        default=1000,
        description="Maximum time allowed for workflow execution in seconds",
    )
