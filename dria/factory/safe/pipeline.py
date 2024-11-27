import logging
from dria.client import Dria
from dria.pipelines import Pipeline
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
from .classify_relevance import ClassifyAtomicFacts
from .rate_with_search import RateWithSearch, NextSearch, NextQuery
from typing import Optional, List, Union, Dict

logger = logging.getLogger(__name__)


class SearchAugmentedFactualityEvaluator:

    def __init__(
        self,
        dria: Dria,
        models: Optional[Union[List[Model], List[List[Model]]]] = None,
    ):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = [
            [
                Model.GPT4O,
                Model.GPT4O_MINI,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.QWEN2_5_72B_OR,
            ],
            [
                Model.GPT4O_MINI,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.GEMINI_15_FLASH,
                Model.GPT4O,
            ],
            [
                Model.GPT4O_MINI,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.LLAMA_3_1_70B_OR,
                Model.GPT4O,
            ],
            [Model.SMALL],
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

    def build(self, question_answer_pairs: List[Dict[str, str]]) -> Pipeline:

        inputs = []
        for pair in question_answer_pairs:
            sentences = self.sentence_splitter(pair["answer"])
            for sentence in sentences:
                inputs.append(
                    {
                        "instruction": prepare_prompt(sentence),
                        "question": pair["question"],
                        "response": pair["answer"],
                    }
                )

        self.pipeline.input(inputs)
        self.pipeline << SplitAtomicFacts().set_models(self.models_list[0])
        self.pipeline << ReviseAtomicFact().set_models(self.models_list[1])
        self.pipeline << ClassifyAtomicFacts().set_models(self.models_list[1])
        self.pipeline << NextQuery().set_models(self.models_list[1])
        self.pipeline << NextSearch().set_models(self.models_list[3])
        self.pipeline << RateWithSearch().set_models(self.models_list[2])

        return self.pipeline.build()
