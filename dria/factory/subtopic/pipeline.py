from typing import List
from dria.client import Dria
from dria.pipelines import (
    PipelineConfig,
    PipelineBuilder,
    Pipeline,
)
from .generate_subtopics.task import GenerateSubtopics
from dria.models import Model
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SubTopicPipeline:
    """
    A pipelines for generating subtopics.

    It is a simple pipelines that generates subtopics based on a given topic.
    Pipeline would create subtopics based on a given topic.
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, topic: str, max_depth=2) -> Pipeline:
        if max_depth < 1:
            raise ValueError("Max depth must be greater than 0")
        self.pipeline.input(topic=topic)
        for i in range(max_depth - 1):
            (
                self.pipeline
                << GenerateSubtopics()
                .set_models([Model.GPT4_TURBO, Model.GEMMA2_9B_FP16])
                .scatter()
            )
        self.pipeline << GenerateSubtopics().set_models(
            [Model.GPT4_TURBO, Model.GEMMA2_9B_FP16]
        )
        return self.pipeline.build()


if __name__ == "__main__":
    _dria = Dria(rpc_token="asd")
    pipeline = SubTopicPipeline(_dria, PipelineConfig())
    pipeline.build(topic="Artificial Intelligence", max_depth=1)
