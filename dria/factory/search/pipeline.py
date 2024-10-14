import logging
from typing import Literal
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .aggregate_pages import PageAggregator
from .summarize import PageSummarizer

logger = logging.getLogger(__name__)


class SearchPipeline:
    """
    A pipeline for searching and retrieving data from web based on a topic
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, topic: str, summarize: bool = False) -> Pipeline:

        self.pipeline.input(topic=topic)
        (
            self.pipeline
            << PageAggregator().set_models(
                [
                    Model.LLAMA3_1_8B_FP16,
                    Model.LLAMA3_1_8BQ8,
                    Model.QWEN2_5_32B_FP16,
                    Model.QWEN2_5_7B_FP16,
                    Model.GPT4O,
                ]
            )
            << PageSummarizer(summarize=summarize).set_models(
                [Model.QWEN2_5_7B_FP16, Model.LLAMA3_1_8B_FP16, Model.QWEN2_5_32B_FP16]
            )
        )
        return self.pipeline.build()
