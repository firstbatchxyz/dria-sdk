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
                [Model.ANTHROPIC_SONNET_3_5_OR, Model.GPT4O, Model.GEMINI_15_PRO]
            )
            .custom()
            << BackStoryStep(chunks=chunks, config=StepConfig())
            .set_models(
                [
                    Model.QWEN2_5_72B_OR,
                    Model.QWEN2_5_7B_OR,
                    Model.QWEN2_5_32B_FP16,
                    Model.LLAMA3_1_8BQ8,
                    Model.QWEN2_5_7B_FP16,
                    Model.ANTHROPIC_HAIKU_3_5_OR,
                    Model.QWEN2_5_EVA_32B_OR,
                    Model.LLAMA_3_1_70B_OR,
                    Model.LLAMA_3_1_8B_OR,
                    Model.GPT4O_MINI,
                    Model.GEMINI_15_FLASH,
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
                    Model.QWEN2_5_7B_OR,
                    Model.QWEN2_5_32B_FP16,
                    Model.MIXTRAL_8_7B,
                    Model.GPT4O_MINI,
                    Model.ANTHROPIC_HAIKU_3_5_OR,
                    Model.GEMINI_15_FLASH,
                    Model.LLAMA_3_1_8B_OR,
                    Model.QWEN2_5_EVA_32B_OR,
                ]
            )
            << AnswerStep(config=StepConfig()).set_models(
                [
                    Model.GEMMA2_9B_FP16,
                    Model.LLAMA_3_1_70B_OR,
                    Model.LLAMA_3_1_8B_OR,
                    Model.LLAMA3_1_8B_FP16,
                    Model.LLAMA_3_1_70B_OR,
                    Model.QWEN2_5_7B_OR,
                    Model.QWEN2_5_32B_FP16,
                    Model.QWEN2_5_EVA_32B_OR,
                    Model.MIXTRAL_8_7B,
                    Model.GPT4O_MINI,
                    Model.GPT4O,
                    Model.GEMINI_15_FLASH,
                    Model.GEMINI_15_PRO,
                    Model.ANTHROPIC_HAIKU_3_5_OR,
                    Model.ANTHROPIC_SONNET_3_5_OR,
                ]
            )
        )
        return self.pipeline.build()
