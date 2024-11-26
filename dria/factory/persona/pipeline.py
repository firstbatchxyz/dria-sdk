import logging
from dria.client import Dria
from dria.pipelines import Pipeline
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
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = [
            [
                Model.GPT4O,
                Model.ANTHROPIC_SONNET_3_5_OR,
                Model.GEMINI_15_PRO,
                Model.LLAMA_3_1_405B_OR,
                Model.LLAMA_3_1_70B_OR,
            ],
            [
                Model.QWEN2_5_7B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.LLAMA3_1_8B_FP16,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.GPT4O_MINI,
                Model.GEMINI_15_FLASH,
                Model.LLAMA_3_1_70B_OR,
            ],
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
    pipeline = PersonaPipeline(_dria)
    pipeline.build(simulation_description="A simulation description", num_samples=100)
