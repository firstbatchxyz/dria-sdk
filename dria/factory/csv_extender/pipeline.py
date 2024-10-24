import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .dependencies import GetDependencies, PopulateDependencies
from .extend import ExtendCSV

logger = logging.getLogger(__name__)


class CSVExtenderPipeline:
    """
    A
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, csv, num_samples=10) -> Pipeline:
        self.pipeline.input(csv=csv, num_samples=num_samples)
        (
            self.pipeline
            << GetDependencies(num_samples=num_samples).set_models([Model.GPT4O, Model.GEMINI_15_PRO]).custom()
            << PopulateDependencies().set_models([Model.GPT4O, Model.GEMINI_15_FLASH, Model.GEMINI_15_PRO]).custom()
            << ExtendCSV().set_models([Model.GPT4O, Model.GEMINI_15_FLASH, Model.GEMINI_15_PRO, Model.QWEN2_5_7B_FP16,
                                       Model.LLAMA3_1_8B_FP16, Model.GEMMA2_9B_FP16, Model.QWEN2_5_32B_FP16]).custom()
        )
        return self.pipeline.build()


