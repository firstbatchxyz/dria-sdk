<p align="center">
  <img src="https://raw.githubusercontent.com/firstbatchxyz/.github/refs/heads/master/branding/dria-logo-square.svg" alt="logo" width="168">
</p>

<h1 align="center">Dria SDK</h1>

<p align="center">
  <a href="https://pypi.org/project/dria/"><img src="https://badge.fury.io/py/dria.svg" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://docs.dria.co"><img src="https://img.shields.io/badge/docs-online-brightgreen.svg" alt="Documentation Status"></a>
      <a href="https://discord.gg/dria" target="_blank">
        <img alt="Discord" src="https://dcbadge.vercel.app/api/server/dria?style=flat">
    </a>
</p>

**Dria SDK** is a scalable and versatile toolkit for creating and managing synthetic datasets for AI. With Dria, you can orchestrate multi-step pipelines that pull data from both web and siloed sources, blend them with powerful AI model outputs, and produce high-quality synthetic datasets—**no GPU required**.  

---

## Why Dria?

- **Dataset Generation**: Easily build synthetic data pipelines using Dria’s flexible APIs.
- **Multi-Agent Network**: Orchestrate complex tasks and data retrieval using specialized agents for web search and siloed APIs.
- **No GPUs Needed**: Offload your compute to the network, accelerating your workflows without personal GPU hardware.
- **Customizable**: Define custom Pydantic schemas to shape the output of your datasets precisely.
- **Model-Rich**: Use different Large Language Models (LLMs) such as OpenAI, Gemini, Ollama or others to synthesize data.
- **Grounding & Diversity**: Add real-world context to your synthetic datasets with integrated web and siloed data retrieval.

---

## Installation

Dria SDK is available on PyPI. You can install it with:
```bash
pip install dria
```

It’s recommended to use a virtual environment (e.g., `virtualenv` or `conda`) to avoid version conflicts with other packages.

---

## Quick Start

Here’s a minimal example to get you started with Dria:

```python
import asyncio
from dria import Prompt, DatasetGenerator, DriaDataset, Model
from pydantic import BaseModel, Field

# 1. Define schema
class Tweet(BaseModel):
    topic: str = Field(..., title="Topic")
    tweet: str = Field(..., title="Tweet")

# 2. Create a dataset
dataset = DriaDataset(name="tweet_test", description="A dataset of tweets!", schema=Tweet)

# 3. Prepare instructions
instructions = [
    {"topic": "BadBadNotGood"},
    {"topic": "Decentralized Synthetic Data"}
]

# 4. Create a Prompt
prompter = Prompt(prompt="Write a tweet about {{topic}}", schema=Tweet)

# 5. Generate data
generator = DatasetGenerator(dataset=dataset)

asyncio.run(
    generator.generate(
        instructions=instructions,
        singletons=prompter,
        models=Model.GPT4O
    )
)

# Convert to Pandas
df = dataset.to_pandas()
print(df)
```

**Output**:
```
                         topic                                              tweet
0                BadBadNotGood  🎶 Thrilled to have discovered #BadBadNotGood! ...
1  Decentralized Synthetic Data  Exploring the future of #AI with decentralized...
```

---

## Usage

### 1. Define Your Dataset Schema

Use [Pydantic](https://pydantic-docs.helpmanual.io/) models to define the structure of your synthetic data. For example:

```python
from pydantic import BaseModel, Field

class Tweet(BaseModel):
    topic: str = Field(..., title="Topic")
    tweet: str = Field(..., title="Tweet")
```

### 2. Create a Dataset

Instantiate a `DriaDataset` by specifying its name, description, and the Pydantic schema:

```python
from dria import DriaDataset

dataset = DriaDataset(name="tweet_test", description="A dataset of tweets!", schema=Tweet)
```

### 3. Write a Prompt

Use `Prompt` objects to define how to generate data from an instruction. You can reference fields using double-curly braces:

```python
from dria import Prompt

prompter = Prompt(
    prompt="Write a tweet about {{topic}}",
    schema=Tweet
)
```

### 4. Generate Synthetic Data

Create a `DatasetGenerator` and call `generate`:

```python
from dria import DatasetGenerator, Model

generator = DatasetGenerator(dataset=dataset)

instructions = [{"topic": "Cats"}, {"topic": "Dogs"}]

await generator.generate(
    instructions=instructions,
    singletons=prompter,
    models=Model.GPT4O  # Example model
)
```

- `instructions`: A list of dictionaries, each used to fill the placeholders in your `Prompt`.
- `singletons`: A single prompt (or list of prompts) that is applied to all instructions.
- `models`: The model or list of models you want to use.

### 5. Convert to Pandas

Finally, convert your generated dataset to a Pandas DataFrame:

```python
import pandas as pd

df = dataset.to_pandas()
print(df)
```

> Dria supports a wide range of data type exports. You can see the full list [here](https://docs.dria.co/how-to/dria_datasets_exports). You will need to have some tokens in your balance, which will be approved automatically if required by the register command.

---

## Advanced Usage

### Available Models

Dria supports a wide range of models from OpenAI, Gemini, Ollama, and more. You can see the full list [here](https://docs.dria.co/how-to/models).

### Writing Workflows and Custom Pipelines

Dria allows you to write custom workflows and pipelines using the `Workflow` class. You can see an example of this [here](https://docs.dria.co/how-to/workflows).


### Structured Outputs

Dria allows you to define custom schemas for your outputs using Pydantic. This allows you to generate highly structured data that can be used for a wide range of applications.

You can see an example of this [here](https://docs.dria.co/how-to/structured_outputs/).

### Parallelization & Offloading

Because Dria tasks can be dispatched to a distributed network of agents, you can leverage **massive parallelization** without owning any GPUs. This is especially helpful for large-scale data generation tasks:
- Avoid timeouts or rate limits by distributing tasks.
- Scale to thousands or millions of records quickly.

---

## Contributing

Contributions are more than welcome! To get started:

1. **Fork** the repository on GitHub.  
2. **Clone** your fork locally and create a new branch for your feature or fix.
3. **Install** dependencies in a virtual environment:  
   ```bash
   poetry install
   ```
4. **Make Changes** and **Test** them thoroughly.
5. **Submit a Pull Request** describing your changes.

We value all contributions—from bug reports and suggestions to feature implementations.

---

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use it in your personal or commercial projects.

---