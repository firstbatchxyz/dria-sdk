from dria.factory import (
    score_complexity,
    evolve_complexity,
    generate_semantic_triple,
    PersonaPipeline,
    SubTopicPipeline,
)
from dria.client import Dria
from dria.pipelines import PipelineConfig

if __name__ == "__main__":

    dria = Dria(rpc_token="token")
    cfg = PipelineConfig()
    pipe = SubTopicPipeline(dria, cfg).build(
        topics=["Artificial Intelligence"], max_depth=2
    )
