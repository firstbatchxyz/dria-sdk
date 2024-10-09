

'PipelineBuilder' builds 'Pipeline'

We need distributor for distributing a large input to a set pipeline or standalone tasks

PipelineBuilder() has inputs: as **kwargs,  name=name, description=description etc.

pipeline = PipelineBuilder(name="pipeline_name", description="pipeline_description")
pipeline << task1 << task2 << task3
pipeline.build()


StepTemplate -> StepBuilder -> Step

what about tasks?

Task1(BaseStepTemplate):

- should have create_workflow() where workflow is written inside
- callback() for custom callbacks
- broadcast(), scatter(), aggregate()  , these callbacks should not be called for the last step of pipeline
- 