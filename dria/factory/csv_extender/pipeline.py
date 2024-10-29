import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .dependencies import GetDependencies, PopulateDependencies
from .extend import ExtendCSV
from typing import Optional, List, Union

logger = logging.getLogger(__name__)


class CSVExtenderPipeline:
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
            [Model.GPT4O, Model.GEMINI_15_PRO],
            [Model.GPT4O, Model.GEMINI_15_FLASH, Model.GEMINI_15_PRO],
            [
                Model.GPT4O,
                Model.GEMINI_15_FLASH,
                Model.GEMINI_15_PRO,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
                Model.GEMMA2_9B_FP16,
                Model.QWEN2_5_32B_FP16,
            ],
        ]
        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 3:
                    raise ValueError(
                        "Models should be a list of two lists for CSVExtenderPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models, models, models]

    def build(self, csv, num_samples=10) -> Pipeline:
        self.pipeline.input(csv=csv, num_samples=num_samples)
        (
            self.pipeline
            << GetDependencies(num_samples=num_samples)
            .set_models(self.models_list[0])
            .custom()
            << PopulateDependencies().set_models(self.models_list[1]).custom()
            << ExtendCSV().set_models(self.models_list[2]).custom()
        )
        return self.pipeline.build()
