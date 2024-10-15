# SubTopicPipeline

`SubTopicPipeline` is a class that creates a pipeline for generating subtopics based on a given topic. The pipeline recursively generates subtopics with increasing depth.

## Class Overview

The `SubTopicPipeline` class has the following components:

- Constructor: Initializes the pipeline with a `Dria` instance and a `PipelineConfig`.
- `build` method: Constructs the pipeline based on the given topic and maximum depth.


```python
import asyncio
import os

from dria.client import Dria
from dria.factory import SubTopicPipeline
from dria.pipelines import PipelineConfig

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    await dria.initialize()
    pipeline = SubTopicPipeline(dria, PipelineConfig()).build(topic="Artificial Intelligence", max_depth=2)
    res = await pipeline.execute(return_output=True)
    print(res)


if __name__ == "__main__":
    asyncio.run(evaluate())
```

Expected Output

```json
{
   "subtopics":[
      "Applications of Deep Learning in Healthcare",
      "Deep Reinforcement Learning for Complex Systems",
      "Transfer Learning for Efficient Model Deployment",
      "Industry-Specific Use Cases and Success Stories",
      "Addressing Bias and Fairness in AI Decision-Making",
      "Future of Work: Human-AI Collaboration and Augmentation",
      "Deep learning basics for industry adoption",
      "Applications of deep learning in computer vision",
      "Natural language processing with deep learning",
      "Generative models and data augmentation",
      "Transfer learning and domain adaptation",
      "Explainability and interpretability techniques",
      "Fairness, bias, and ethics in AI",
      "Real-world case studies and success stories",
      "Deep learning for robotics and automation",
      "Neural networks for predictive maintenance",
      "Human-centered design and user experience",
      "Emergence of Deep Learning Techniques",
      "Key Applications of Machine Learning",
      "Current State of AutoML Research",
      "Ethical Implications of AI Decision Making",
      "Predicting Human Behavior with ML Models",
      "Future Directions for Natural Language Processing",
      "History of Neural Networks",
      "Supervised vs Unsupervised Learning",
      "Deep Learning Techniques and Algorithms",
      "Machine Learning in Healthcare Applications",
      "Bias and Fairness in Machine Learning Models",
      "Explainable AI and Model Interpretation",
      "Early life of Geoffrey Hinton",
      "Educational background and influences",
      "Key milestones in his career",
      "Breakthroughs in deep learning",
      "Impact on artificial intelligence research",
      "Notable awards and recognition",
      "Contributions to neural networks",
      "Teaching career and legacy",
      "Historical background of AI development",
      "Key theories and concepts in AI ethics",
      "Current research and advancements in AI",
      "Practical applications of AI in industry",
      "Debates surrounding AI job displacement",
      "Ethics of AI decision-making and bias",
      "Regulatory frameworks for AI development",
      "Future trends and predictions for AI development",
      "The role of humans in AI decision-making",
      "Social implications of AI adoption"
   ]
}
```