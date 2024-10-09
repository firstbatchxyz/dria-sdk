from .task import MagPie
import logging
from typing import Optional, List
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model

logger = logging.getLogger(__name__)


class DialoguePipeline:
    """
    A pipelines for generating personas.

    It is a simple pipelines that generates personas based on a simulation description.
    Pipeline would create random variables that fit into the simulation description.
    Then it would generate a backstory for each sample.
    Number of samples can be specified to determine the number of personas to be generated.
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(
        self,
        instructor_persona: str,
        responding_persona: str,
        num_turns: int = 2,
        speakers: Optional[List[str]] = None,
    ) -> Pipeline:
        self.pipeline.input(
            instructor_persona=instructor_persona, responding_persona=responding_persona
        )

        self.pipeline << MagPie(num_turns=num_turns, speakers=speakers).set_models(
            [Model.QWEN2_5_7B_FP16]
        )

        return self.pipeline.build()
