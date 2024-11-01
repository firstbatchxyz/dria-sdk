import logging
from typing import Optional, List, Union, Literal
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig, StepConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .aggregate_pages import PageAggregator
from .scrape import PageScraper

logger = logging.getLogger(__name__)


class SearchPipeline:
    """
    A pipeline for searching and retrieving data from web based on a topic
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
            [
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.GEMINI_15_FLASH,
                Model.LLAMA3_2_3B
            ],
            [
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.GEMINI_15_FLASH,
                Model.LLAMA3_2_3B
            ],
        ]

        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 2:
                    raise ValueError(
                        "Models should be a list of two lists for CSVExtenderPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models, models]

    def build(self, topic: str, summarize: bool = False) -> Pipeline:

        self.pipeline.input(topic=topic)
        (
            self.pipeline
            << PageAggregator().set_models(self.models_list[0])
            << PageScraper(config=StepConfig(min_compute=0.85)).set_models(self.models_list[1])
        )

        if summarize:
            pass
        return self.pipeline.build()
