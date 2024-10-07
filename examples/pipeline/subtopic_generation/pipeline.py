from typing import List

from dria.client import Dria
from dria.models import Model, TaskInput
from dria.pipelines import PipelineConfig, StepConfig, PipelineBuilder, StepBuilder, Pipeline
from workflows import GenerateSubtopics, GenerateEntries
import logging




logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SubTopicPipeline:
    """
    A pipeline for generating subtopics.

    It is a simple pipeline that generates subtopics based on a given topic.
    Pipeline would create subtopics based on a given topic.
    """
    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, topics: List[str], max_depth=2) -> Pipeline:
        self.pipeline.input(topics=topics)
        for i in range(max_depth):
            self.pipeline << GenerateSubtopics().scatter()
        self.pipeline << GenerateEntries().aggregate()
        return self.pipeline.build()


if __name__ == "__main__":
    _dria = Dria(rpc_token="asd")
    pipeline = SubTopicPipeline(_dria, PipelineConfig())
    pipeline.build(topics=["Artificial Intelligence"], max_depth=2)