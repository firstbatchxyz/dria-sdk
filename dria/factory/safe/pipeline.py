import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .atomic_facts import (
    prepare_prompt,
    detect_initials,
    fix_sentence_splitter,
    tokenize,
    SplitAtomicFacts,
)
from .revise import ReviseAtomicFact
from typing import Optional, List, Union

logger = logging.getLogger(__name__)


class SearchAugmentedFactualityEvaluator:

    def __init__(
        self,
        dria: Dria,
        config: PipelineConfig,
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)
        self.models_list = [
            [Model.GPT4O, Model.ANTHROPIC_HAIKU_3_5_OR, Model.QWEN2_5_72B_OR],
            [Model.GPT4O_MINI, Model.ANTHROPIC_HAIKU_3_5_OR, Model.GEMINI_15_FLASH],
        ]

        if models:
            # check if models are list of lists, or lists
            if isinstance(models[0], list):
                if len(models) != 2:
                    raise ValueError(
                        "Models should be a list of two lists for PersonaPipeline"
                    )
                self.models_list = models
            else:
                self.models_list = [models, models]

    @staticmethod
    def sentence_splitter(paragraph):
        initials = detect_initials(paragraph)
        curr_sentences = tokenize.sent_tokenize(paragraph)
        return fix_sentence_splitter(curr_sentences, initials)

    def build(self, response: str) -> Pipeline:

        sentences = self.sentence_splitter(response)
        self.pipeline.input(
            [
                {"instruction": prepare_prompt(sentence), "response": response}
                for sentence in sentences
            ]
        )
        self.pipeline << SplitAtomicFacts().set_models(self.models_list[0])
        self.pipeline << ReviseAtomicFact().set_models(self.models_list[1])

        return self.pipeline.build()
