from dria.client import Dria
from dria.pipelines import (
    PipelineBuilder,
    Pipeline,
)
from .subtopics import NemotronSubtopicStep
from .questions import NemotronQuestionStep
from .answers import NemotronAnswerStep
from dria.models import Model


class NemotronQA:
    def __init__(self, dria: Dria):
        self.pipeline = PipelineBuilder(dria)
        self.models_list = [
            [
                Model.GPT4O,
                Model.GEMINI_15_PRO,
                Model.ANTHROPIC_SONNET_3_5_OR,
                Model.LLAMA_3_1_405B_OR,
            ],
            [
                Model.GPT4O_MINI,
                Model.QWEN2_5_32B_FP16,
                Model.GEMINI_15_FLASH,
                Model.MIXTRAL_8_7B,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
                Model.QWEN2_5_EVA_32B_OR,
                Model.QWEN2_5_7B_OR,
                Model.LLAMA_3_1_8B_OR,
                Model.ANTHROPIC_HAIKU_3_5_OR,
            ],
            [
                Model.GEMINI_15_FLASH,
                Model.GEMINI_15_PRO,
                Model.GPT4O,
                Model.ANTHROPIC_HAIKU_3_5_OR,
                Model.ANTHROPIC_SONNET_3_5_OR,
                Model.LLAMA_3_1_70B_OR,
                Model.QWEN2_5_72B_OR,
            ],
        ]

    def build(self, topic: str, n_subtopics: str, n_questions: str) -> Pipeline:

        self.pipeline.input(topic=topic, n_subtopics=n_subtopics)
        (
            self.pipeline
            << NemotronSubtopicStep(n_questions=n_questions)
            .set_models(self.models_list[0])
            .custom()
        )
        self.pipeline << NemotronQuestionStep().set_models(self.models_list[1]).custom()
        self.pipeline << NemotronAnswerStep().set_models(self.models_list[2]).custom()

        return self.pipeline.build()
