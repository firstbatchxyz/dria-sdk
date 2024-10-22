import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from typing import List
from .extender import ListExtender
from .generate_subtopics import GenerateSubtopics

logger = logging.getLogger(__name__)


class ListExtenderPipeline:
    """
    A
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, list: List[str], granularize: bool = False) -> Pipeline:
        self.pipeline.input(e_list=list)

        self.pipeline << ListExtender().set_models([Model.GPT4O, Model.GEMINI_15_FLASH, Model.GEMINI_15_PRO, Model.QWEN2_5_32B_FP16, Model.QWEN2_5_7B_FP16, Model.QWEN2_5_7B, Model.LLAMA3_1_8B_FP16, Model.LLAMA3_1_8BQ8]).custom()

        if granularize:
            self.pipeline << GenerateSubtopics().set_models([Model.GPT4O, Model.GEMINI_15_FLASH, Model.GEMINI_15_PRO, Model.QWEN2_5_32B_FP16, Model.QWEN2_5_7B_FP16, Model.QWEN2_5_7B, Model.LLAMA3_1_8B_FP16, Model.LLAMA3_1_8BQ8]).custom()
        return self.pipeline.build()


