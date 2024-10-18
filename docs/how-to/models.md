# Selecting Models

Dria Network is a network of LLMs, a MoA (Mixture-of-Agents) infrastructure by nature. 
When a task is published to the network, you can specify which models you want to assign your task to.

`Model` enum provides a list of models that you can use in your tasks.

```python
from dria.models import Model
```

`Task` has `models`param to assign models to your task.

Following task will be execued by `LLAMA3_1_8B_FP16` model. If the model is not available within network, SDK will poll the network until it finds an available `LLAMA3_1_8B_FP16` model.
```python
Task(
    workflow=simple.workflow(prompt="Hey there!").model_dump(),
    models=[Model.LLAMA3_1_8B_FP16],
)
```

**Model Availability?**

Dria Network consists of multiple nodes, each running one or more available models. When a task is published, nodes with the selected model execute the task asynchronously.

For example, if the network has 100 `Llama3.2-3B` models, publishing a task with the `Llama3.2-3B` model will be handled by one of those models. 
Publishing 100 tasks will distribute each to one of the 100 available models. 
However, if you publish a 101st task, task will wait in queue until a `Llama3.2-3B` model becomes available.

**Singe Task, Multiple Models**

Dria SDK enables you to publish a single task to multiple models. 
This is useful when you want to compare the results of different models on the same task.
Following example asks the same question to 10 available open-source LLM and returns the results.


```python
async def evaluate():
    simple = Simple()
    task = Task(
        workflow=simple.workflow(
            prompt="What is Solomonoff Induction? Explain shortly."
        ).model_dump(),
        models=[Model.OLLAMA],
    )
    res = await dria.execute(
        task=[task] * 10,
        timeout=200,
    )
    return simple.parse_result(res)
```

Here is a list of models that you can use in your tasks:

```python
# Ollama models
NOUS_THETA = "finalend/hermes-3-llama-3.1:8b-q8_0"
PHI3_MEDIUM = "phi3:14b-medium-4k-instruct-q4_1"
PHI3_MEDIUM_128K = "phi3:14b-medium-128k-instruct-q4_1"
PHI3_5_MINI = "phi3.5:3.8b"
PHI3_5_MINI_FP16 = "phi3.5:3.8b-mini-instruct-fp16"
GEMMA2_9B = "gemma2:9b-instruct-q8_0"
GEMMA2_9B_FP16 = "gemma2:9b-instruct-fp16"
LLAMA3_1 = "llama3.1:latest"
LLAMA3_1_8BQ8 = "llama3.1:8b-instruct-q8_0"
LLAMA3_1_8B_FP16 = "llama3.1:8b-instruct-fp16"
LLAMA3_1_70B = "llama3.1:70b-instruct-q4_0"
LLAMA3_1_70BQ8 = "llama3.1:70b-instruct-q8_0"
LLAMA3_2_1B = "llama3.2:1b"
LLAMA3_2_3B = "llama3.2:3b"
QWEN2_5_7B = "qwen2.5:7b-instruct-q5_0"
QWEN2_5_7B_FP16 = "qwen2.5:7b-instruct-fp16"
QWEN2_5_32B_FP16 = "qwen2.5:32b-instruct-fp16"
QWEN2_5_CODER_1_5B = "qwen2.5-coder:1.5b"
DEEPSEEK_CODER_6_7B = "deepseek-coder:6.7b"
MIXTRAL_8_7B = "mixtral:8x7b"

# Gemini models
GEMINI_15_PRO = "gemini-1.5-pro"
GEMINI_15_FLASH = "gemini-1.5-flash"
GEMINI_10_PRO = "gemini-1.0-pro"
GEMMA_2_2B_IT = "gemma-2-2b-it"
GEMMA_2_9B_IT = "gemma-2-9b-it"
GEMMA_2_27B_IT = "gemma-2-27b-it"

# OpenAI models
GPT4_TURBO = "gpt-4-turbo"
GPT4O = "gpt-4o"
GPT4O_MINI = "gpt-4o-mini"
O1_MINI = "o1-mini"
O1_PREVIEW = "o1-preview"
```

You can also select providers as your models.
```python
# Providers
OLLAMA = "ollama"  # Open source models
OPENAI = "openai"  # OpenAI models
GEMINI = "gemini"  # Gemini models
CODER = "coder"  # Coder models
```