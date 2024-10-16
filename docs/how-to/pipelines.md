# Pipelines

Pipelines are used to generate complex outputs by combining multiple [workflows](how-to/workflows.md). 
The `Pipeline` class is used to define the list of workflows, their corresponding models and the input data.

```python
from dria.pipelines import Pipeline, PipelineConfig, PipelineBuilder
class BasicPipeline:

    def __init__(self, dria: Dria, config: PipelineConfig):
        self.pipeline_config: PipelineConfig = config or PipelineConfig()
        self.pipeline = PipelineBuilder(self.pipeline_config, dria)

    def build(self, instruction: str) -> Pipeline:
        
        self.pipeline.input(instruction=instruction)
        self.pipeline << FirstPipelineStep().scatter() << SecondPipelineStep()
        return self.pipeline.build()
```

`BasicPipeline` has two steps: `FirstPipelineStep` and `SecondPipelineStep` which are instances of `StepTemplate`. 
We use `<<` notation to add multiple steps to the pipeline and determine the order of execution. 

Let's define the work done by `FirstPipelineStep` and `SecondPipelineStep`:

`FirstPipelineStep`: 
```python
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, GetAll, Workflow
from dria.pipelines import StepTemplate


class FirstPipelineStep(StepTemplate):
    def create_workflow(self, instruction: str) -> Workflow:

        builder = WorkflowBuilder(instruction=instruction)

        builder.generative_step(
            id="generate_variations",
            path="Rewrite 5 variations of given instruction by making small changes. Instruction: {{instruction}}. Output a single Python list for new instructions, and nothing else. New instructions:",
            operator=Operator.GENERATION,
            outputs=[Write.new("variations")],
        )

        flow = [Edge(source="generate_variations", target="_end")]
        builder.flow(flow)
        builder.set_return_value("variations")
        workflow = builder.build()
        return workflow
```

`FirstPipelineStep` generates 5 variations of the given instruction. 
Instruction: `Write a haiku`
Output:
```json
[
   "write a Japanese-style haiku",
   "compose a three-line poem",
   "craft a traditional tanka",
   "create a nature-inspired haiku",
   "draft a short, 5-7-5 syllable poem"
]
```

For the second step, `SecondPipelineStep`, we will use the output of the first step as input. 

```python
class SecondPipelineStep(StepTemplate):
    def create_workflow(self, instruction: str) -> Workflow:

        builder = WorkflowBuilder(instruction=instruction)

        builder.generative_step(
            id="execute_instruction",
            path="{{instruction}}",
            operator=Operator.GENERATION,
            outputs=[Write.new("output")],
        )

        flow = [Edge(source="execute_instruction", target="_end")]
        builder.flow(flow)
        builder.set_return_value("output")
        workflow = builder.build()
        return workflow
```

Instead looping through variations generated in the first step, and executing them one-by-one, we use special `scatter` callback to execute them in parallel.
Pipeline will automatically handle the parallel execution of the steps by parsing the json output and sending each instruction as a seperate task to network.

Finally we set the input instruction using the `input` method. and build the pipeline 

#### Callbacks

Callbacks are executed after a step is finished. Dria provides three built-in callbacks:

1. `scatter`: 1-N mapping of input to output. Used to execute multiple tasks in parallel. Suitable when a step output is a list.
2. `broadcast`: 1-N mapping of input to output. Used to duplicate the input to multiple tasks. Suitable when a step output is a single value.
3. `aggregate`: N-1 mapping of input to output. Used to combine multiple outputs into a single output. Suitable when a step output is a list.

```python
self.pipeline << FirstPipelineStep().scatter() << SecondPipelineStep()
```

*Custom Callbacks*: You can define custom callbacks by implementing the `callback` method for `StepTemplate` class. 

Custom callback takes a `Step` object as input and returns a `TaskInput` or  `List[TaskInput]`. Custom callbacks enable design of custom input-output matching between steps of the pipeline.
Here is an example of a custom callback:

```python
def callback(self, step: "Step") -> Union[List[TaskInput], TaskInput]:
    """
    Only to use as the last callback
    Args:
        step:

    Returns:

    """
    # flatten list of lists
    outputs = [parse_json(o.result) for o in step.output]
    flattened = [item for sublist in outputs for item in sublist]
    return TaskInput(**{"subtopics": flattened})
```

Callback above flattens the list of lists and returns a single `TaskInput` object.
An important point to note is that custom callbacks keys should match the keys of the input of the next step in the pipeline.
For our case, the next step should have a key `subtopics` in its input.