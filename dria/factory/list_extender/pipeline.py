import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from typing import List
from .extender import ListExtender
from .generate_subtopics import GenerateSubtopics
from typing import Optional, List, Union

logger = logging.getLogger(__name__)


class ListExtenderPipeline:
    """
    A
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
                Model.GPT4O,
                Model.GEMINI_15_FLASH,
                Model.GEMINI_15_PRO,
                Model.QWEN2_5_32B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.QWEN2_5_7B,
                Model.LLAMA3_1_8B_FP16,
                Model.LLAMA3_1_8BQ8,
            ],
            [
                Model.GPT4O,
                Model.GEMINI_15_FLASH,
                Model.GEMINI_15_PRO,
                Model.QWEN2_5_32B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.QWEN2_5_7B,
                Model.LLAMA3_1_8B_FP16,
                Model.LLAMA3_1_8BQ8,
            ],
        ]

        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 2:
                    raise ValueError(
                        "Models should be a list of two lists for ListExtenderPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models, models]

    def build(self, list: List[str], granularize: bool = False) -> Pipeline:
        self.pipeline.input(e_list=list)

        self.pipeline << ListExtender().set_models(self.models_list[0]).custom()

        if granularize:
            (
                self.pipeline
                << GenerateSubtopics().set_models(self.models_list[1]).custom()
            )
        return self.pipeline.build()
