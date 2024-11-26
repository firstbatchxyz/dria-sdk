from typing import Optional, List, Union
from dria.client import Dria
from dria.pipelines import (
    PipelineBuilder,
    Pipeline,
)
from .generate_subtopics.task import GenerateSubtopics
from dria.models import Model
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SubTopicPipeline:
    """
    A pipelines for generating subtopics.

    It is a simple pipelines that generates subtopics based on a given topic.
    Pipeline would create subtopics with recursively increasing depth.
    """

    def __init__(
        self,
        dria: Dria,
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = [
            [
                Model.LLAMA3_1_8BQ8,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.GEMMA2_9B_FP16,
                Model.LLAMA3_2_3B,
                Model.GPT4O_MINI,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.QWEN2_5_7B_OR,
                Model.GEMINI_15_FLASH,
            ]
        ]

        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 1:
                    raise ValueError(
                        "Models should be a list of one list for SubTopicPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models]

    def build(self, topic: str, max_depth=2) -> Pipeline:
        if max_depth < 1:
            raise ValueError("Max depth must be greater than 0")
        self.pipeline.input(topic=topic)
        for i in range(max_depth - 1):
            (
                self.pipeline
                << GenerateSubtopics().set_models(self.models_list[0]).scatter()
            )
        self.pipeline << GenerateSubtopics().set_models(
            [
                Model.LLAMA3_1_8BQ8,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_7B_FP16,
                Model.QWEN2_5_32B_FP16,
                Model.GEMMA2_9B_FP16,
                Model.LLAMA3_2_3B,
                Model.LLAMA_3_1_8B_OR,
                Model.GPT4O_MINI,
                Model.QWEN2_5_7B_OR,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.DEEPSEEK_2_5_OR,
                Model.LLAMA_3_1_70B_OR,
            ]
        )
        return self.pipeline.build()


if __name__ == "__main__":
    _dria = Dria(rpc_token="asd")
    pipeline = SubTopicPipeline(_dria)
    pipeline.build(topic="Artificial Intelligence", max_depth=1)
