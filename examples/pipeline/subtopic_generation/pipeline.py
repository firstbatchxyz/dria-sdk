from dria.client import Dria
from dria.models import Model, TaskInput
from dria.pipelines import PipelineConfig, StepConfig, PipelineBuilder, StepBuilder
from workflows import generate_entries, generate_subtopics


async def create_subtopic_pipeline(dria: Dria, topic, config: PipelineConfig = PipelineConfig(), max_depth=1):
    pipeline = PipelineBuilder(config, dria)
    depth = 0

    # handles single topic output
    subtopics = StepBuilder(input=TaskInput(topics=[topic]), config=StepConfig(models=[Model.QWEN2_5_7B_FP16,
                                                                                       Model.GPT4O]),
                            workflow=generate_subtopics).broadcast().build()
    pipeline.add_step(subtopics)

    while depth < max_depth:
        # handles multiple topics
        subtopics = StepBuilder(workflow=generate_subtopics,
                                config=StepConfig(models=[Model.QWEN2_5_7B_FP16, Model.GPT4O])).scatter().build()
        pipeline.add_step(subtopics)
        depth += 1

    # entry generation
    entries = StepBuilder(workflow=generate_entries, config=StepConfig(min_compute=0.8)).build()
    pipeline.add_step(entries)
    return pipeline.build()
