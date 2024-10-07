import logging
from typing import Any, List

from dria.client import Dria
from dria.models import Model
from dria.models.models import TaskInput
from dria.pipelines import PipelineConfig, StepConfig
from dria.pipelines.builder import PipelineBuilder, StepBuilder, Pipeline
from examples.pipeline.persona.backstory.task import BackStory
from examples.pipeline.persona.random_variables.task import RandomVariable

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PersonaPipeline:
    """
    A pipeline for generating personas.

    It is a simple pipeline that generates personas based on a simulation description.
    Pipeline would create random variables that fit into the simulation description.
    Then it would generate a backstory for each sample.
    Number of samples can be specified to determine the number of personas to be generated.
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, simulation_description: str, num_samples: int) -> Pipeline:
        self.pipeline.input(simulation_description=simulation_description)
        (
            self.pipeline
            << RandomVariable(num_samples=num_samples).scatter()
            << BackStory()
        )
        return self.pipeline.build()


if __name__ == "__main__":
    _dria = Dria(rpc_token="asd")
    pipeline = PersonaPipeline(_dria, PipelineConfig())
    pipeline.build(simulation_description="A simulation description", num_samples=100)
