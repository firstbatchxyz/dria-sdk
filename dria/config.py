from pydantic import BaseModel, Field


class DriaConfig(BaseModel):
    return_deadline: int = Field(default=86400,
                                 description="The deadline for returning results in seconds. If the deadline is "
                                             "exceeded, output will be ignored.")

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True
