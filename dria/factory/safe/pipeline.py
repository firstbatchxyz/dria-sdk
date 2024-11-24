import logging
from dria.client import Dria
from dria.pipelines import Pipeline, PipelineConfig
from dria.pipelines.builder import PipelineBuilder
from dria.models import Model
from .atomic_facts import detect_initials, fix_sentence_splitter, tokenize, SplitAtomicFacts
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
            [Model.GPT4O],
            [Model.QWEN2_5_7B_FP16, Model.QWEN2_5_32B_FP16, Model.LLAMA3_1_8B_FP16],
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

    def build(self, paragraph: str) -> Pipeline:

        sentences = self.sentence_splitter(paragraph)

        self.pipeline.input([{"sentence":sentence, "paragraph":paragraph} for sentence in sentences])
        self.pipeline << SplitAtomicFacts().set_models(self.models_list[0])

        return self.pipeline.build()
