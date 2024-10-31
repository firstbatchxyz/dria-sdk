import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .backstory.task import BackStory
from .random_variables.task import RandomVariable
from typing import Optional, List, Union

logger = logging.getLogger(__name__)


class PersonaPipeline:
    """
    A pipelines for generating personas.

    It is a simple pipelines that generates personas based on a simulation description.
    Pipeline would create random variables that fit into the simulation description.
    Then it would generate a backstory for each sample.
    Number of samples can be specified to determine the number of personas to be generated.
    """

    def __init__(
        self,
        dria: Dria,
        config: PipelineConfig,
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)
        self.models_list = [
            [Model.GPT4O],
            [Model.QWEN2_5_7B_FP16, Model.QWEN2_5_32B_FP16, Model.LLAMA3_1_8B_FP16],
        ]

        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 2:
                    raise ValueError(
                        "Models should be a list of two lists for PersonaPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models, models]

    def build(self, simulation_description: str, num_samples: int) -> Pipeline:
        self.pipeline.input(simulation_description=simulation_description)
        (
            self.pipeline
            << RandomVariable(num_samples=num_samples).set_models(self.models_list[0])
            << BackStory().set_models(self.models_list[1])
        )
        return self.pipeline.build()


if __name__ == "__main__":
    _dria = Dria(rpc_token="asd")
    pipeline = PersonaPipeline(_dria, PipelineConfig())
    pipeline.build(simulation_description="A simulation description", num_samples=100)
