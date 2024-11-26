import logging
from typing import Optional, List, Union, Literal
from dria.client import Dria
from dria.pipelines import Pipeline, StepConfig
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
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = [
            [
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.ANTHROPIC_SONNET_3_5_OR,
                Model.LLAMA_3_1_70B_OR,
                Model.LLAMA_3_1_8B_OR,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.GEMINI_15_FLASH,
                Model.GPT4O_MINI,
                Model.GPT4O,
            ],
            [
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.GEMINI_15_FLASH,
                Model.GPT4O_MINI,
                Model.GPT4O,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.ANTHROPIC_SONNET_3_5_OR,
                Model.LLAMA_3_1_70B_OR,
                Model.LLAMA_3_1_8B_OR,
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
            << PageScraper(config=StepConfig(min_compute=0.9)).set_models(
                self.models_list[1]
            )
        )

        if summarize:
            pass
        return self.pipeline.build()
