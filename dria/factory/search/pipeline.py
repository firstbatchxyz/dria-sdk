import logging
from typing import Literal
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .aggregate_pages import PageAggregator
from dria.factory.subtopic.generate_subtopics import SubtopicGenerator
from .summarize import PageSummarizer

logger = logging.getLogger(__name__)

Granularization = Literal["None", "Narrow", "Wide"]


class SearchPipeline:
    """
    A pipeline for searching and retrieving data from web based on a topic..

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
        topic: str,
        summarize: bool = False,
        granularization: Granularization = "None",
    ) -> Pipeline:

        self.pipeline.input(topic=topic)
        (
            self.pipeline
            << PageAggregator().set_models(
                [
                    Model.LLAMA3_1_8B_FP16,
                    Model.QWEN2_5_32B_FP16,
                    Model.QWEN2_5_7B_FP16,
                    Model.GPT4O,
                ]
            )
            << PageSummarizer(summarize=summarize).set_models(
                [Model.QWEN2_5_7B_FP16, Model.GEMMA2_9B_FP16, Model.LLAMA3_1_8B_FP16]
            )
        )
        return self.pipeline.build()
