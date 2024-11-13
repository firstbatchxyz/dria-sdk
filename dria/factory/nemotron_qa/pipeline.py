from dria.client import Dria
from dria.pipelines import (
    PipelineConfig,
    PipelineBuilder,
    Pipeline,
)
from .subtopics import NemotronSubtopicStep
from .questions import NemotronQuestionStep
from .answers import NemotronAnswerStep
from dria.models import Model


class NemotronQA:
    def __init__(self, dria: Dria):
        self.pipeline_config: PipelineConfig = PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)
        self.models_list = [
            [Model.GPT4O],
            [
                Model.GPT4O_MINI,
                Model.QWEN2_5_32B_FP16,
                Model.GEMINI_15_FLASH,
                Model.MIXTRAL_8_7B,
                Model.QWEN2_5_7B_FP16,
                Model.LLAMA3_1_8B_FP16,
            ],
            [
                Model.O1_MINI,
                Model.GEMINI_15_FLASH,
                Model.GEMINI_15_PRO,
                Model.GPT4O,
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
