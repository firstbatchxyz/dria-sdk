import logging
from typing import List

from dria.client import Dria
from dria.models import Model
from dria.pipelines import PipelineConfig, Pipeline, StepConfig
from dria.pipelines.builder import PipelineBuilder

from .answer import AnswerStep
from .questions import QuestionStep
from .random_vars import RandomVarsStep
from .backstory import BackStoryStep

logger = logging.getLogger(__name__)


class QAPipeline:
    """
    A pipeline for generating QA pairs
    """

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(
        self,
        simulation_description: str,
        num_samples: int,
        persona: str,
        chunks: List[str],
    ) -> Pipeline:
        self.pipeline.input(simulation_description=simulation_description)
        (
            self.pipeline
            << RandomVarsStep(
                num_of_samples=num_samples, config=StepConfig(max_tokens=1500)
            )
            .set_models(
                [Model.GPT4_TURBO, Model.GPT4O, Model.O1_MINI, Model.GEMINI_15_PRO]
            )
            .custom()
            << BackStoryStep(chunks=chunks, config=StepConfig())
            .set_models(
                [
                    Model.GEMMA2_9B,
                    Model.GEMMA2_9B_FP16,
                    Model.LLAMA3_1_8BQ8,
                    Model.LLAMA3_1_8B_FP16,
                    Model.QWEN2_5_7B,
                    Model.QWEN2_5_7B_FP16,
                    Model.QWEN2_5_32B_FP16,
                    Model.MIXTRAL_8_7B,
                    Model.GPT4_TURBO,
                    Model.GPT4O,
                    Model.GEMINI_15_FLASH,
                    Model.GEMINI_15_PRO,
                ]
            )
            .custom()
            << QuestionStep(persona=persona, config=StepConfig()).set_models(
                [
                    Model.GEMMA2_9B,
                    Model.GEMMA2_9B_FP16,
                    Model.LLAMA3_1_8BQ8,
                    Model.LLAMA3_1_8B_FP16,
                    Model.QWEN2_5_7B,
                    Model.QWEN2_5_7B_FP16,
                    Model.QWEN2_5_32B_FP16,
                    Model.MIXTRAL_8_7B,
                    Model.GPT4_TURBO,
                    Model.GPT4O,
                    Model.GEMINI_15_FLASH,
                    Model.GEMINI_15_PRO,
                ]
            )
            << AnswerStep(config=StepConfig()).set_models(
                [
                    Model.GEMMA2_9B,
                    Model.GEMMA2_9B_FP16,
                    Model.LLAMA3_1_8BQ8,
                    Model.LLAMA3_1_8B_FP16,
                    Model.QWEN2_5_7B,
                    Model.QWEN2_5_7B_FP16,
                    Model.QWEN2_5_32B_FP16,
                    Model.MIXTRAL_8_7B,
                    Model.GPT4_TURBO,
                    Model.GPT4O,
                    Model.GEMINI_15_FLASH,
                    Model.GEMINI_15_PRO,
                ]
            )
        )
        return self.pipeline.build()
