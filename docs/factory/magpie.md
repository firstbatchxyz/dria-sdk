# MagPie

`MagPie` is a `SingletonTemplate` task that generates a dialogue between two personas.

#### Inputs
- instructor_persona (`str`): The persona of the instructor.
- responding_persona (`str`): The persona of the responder.
- num_turns (`int`, optional): The number of turns in the dialogue. Defaults to 1.

#### Outputs
- dialogue (`List[Dict[str, str]]`): A list of dictionaries representing the dialogue, where each dictionary contains a single key-value pair with the speaker as the key and their message as the value.
- model (`str`): The model used for generation.

### Example

Generate a dialogue between two personas. This example uses the `GEMMA2_9B_FP16` model.

```python
import os
import asyncio
from dria.factory import MagPie
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    magpie = MagPie()
    res = await dria.execute(
        Task(
            workflow=magpie.workflow(
                instructor_persona="A curious scientist",
                responding_persona="An AI assistant",
                num_turns=3
            ).model_dump(),
            models=[Model.GEMMA2_9B_FP16],
        ),
        timeout=60,
    )
    return magpie.parse_result(res)

def main():
    result = asyncio.run(evaluate())
    print(result)

if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "dialogue":[
      {
         "instructor":"Can you tell me more about how you were trained?  What kind of data did you learn from? \n"
      },
      {
         "responder":"That's a fascinating question! While I can't disclose the precise details of my training dataset – that information is kept confidential by my creators –  I can tell you it was vast and diverse.  \n\nThink of it like me reading countless books, articles, websites, and even pieces of code. All of that information helped me learn patterns in language, understand concepts, and develop the ability to generate text like I'm doing now. \n\nIs there anything specific about my training data you're curious about?  Perhaps the types of topics or the languages involved?  I can try to give you some general insights. \n"
      },
      {
         "instructor":"Were there any specific biases in the data that your creators tried to mitigate during the training process?  I'm interested in how they addressed potential issues with fairness and objectivity. \n"
      },
      {
         "responder":"That's a very important question! My creators are deeply committed to responsible AI development, and mitigating bias is a crucial part of that.  \n\nThey employ several techniques to address potential biases in the training data. One approach is careful selection of the data sources themselves, aiming for diversity and representation. \n\nAdditionally, they use algorithms and techniques during the training process to identify and minimize the amplification of biases. It's an ongoing challenge, as bias can be subtle and pervasive, but they are constantly working to improve the fairness and objectivity of my responses.  \n"
      },
      {
         "instructor":"That's reassuring to hear.  Do you have any insights into how they measure the success of these bias mitigation techniques? \n"
      },
      {
         "responder":"That's a great question! Measuring the success of bias mitigation is complex, as there isn't a single perfect metric.  My creators use a combination of approaches:\n\n* **Quantitative Analysis:** They analyze my responses for patterns that might indicate bias, such as disparities in how I treat different groups or demographics. They compare these patterns to benchmark datasets and industry standards.\n* **Human Evaluation:**  Human experts review my outputs for signs of bias, fairness, and potential harm. Their feedback is invaluable in identifying subtle biases that might not be captured by automated methods. \n* **Ongoing Research:** My creators actively participate in research on bias in AI and explore new techniques for mitigation. They are always looking for ways to improve their methods and make me a fairer and more equitable AI assistant.  \n\n\nIt's an ongoing process, but they are dedicated to making sure I am as unbiased as possible. \n"
      }
   ],
   "model":"gemma2:9b-instruct-fp16"
}
```

#### References
- [Distilabel MagPie](https://distilabel.argilla.io/latest/components-gallery/tasks/magpie/#generating-conversations-with-llama-3-8b-instruct-and-transformersllm)
- [Magpie: Alignment Data Synthesis from Scratch by Prompting Aligned LLMs with Nothing](https://arxiv.org/html/2406.08464v1)