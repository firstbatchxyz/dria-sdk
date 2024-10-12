# WebMultiChoice

`WebMultiChoice` is a `SingletonTemplate` task that answers multiple-choice questions using web search and evaluation.

#### Inputs
- question (`str`): The multiple-choice question to be answered.
- choices (`List[str]`): A list of possible answer choices for the question.

#### Outputs
- answer (`str`): The evaluated answer to the multiple-choice question.
- model (`str`): The model used to generate the answer.

### Workflow Steps

1. Generate a web search query based on the question and choices.
2. Select a URL from the search results.
3. Scrape content from the selected URL.
4. Generate notes based on the scraped content and the question.
5. Evaluate the notes and choices to determine the best answer.

### Example

Answer a multiple-choice question using web search and evaluation. This example uses the `QWEN2_5_7B_FP16` model.

```python
import os
import asyncio
from dria.factory import WebMultiChoice
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    web_multi_choice = WebMultiChoice()
    question = "A 26-year-old gravida 2 para 1 at 24 weeks gestation is admitted to the labor and delivery suite with mild abdominal cramps, uterine contractions, and a watery vaginal discharge. She has a history of preterm birth. The vital signs are as follows: blood pressure 125/80 mm Hg; heart rate 100/min; respiratory rate 13/min; and temperature 36.6℃ (97.9℉). The pelvic examination reveals cervical softening and shortening. Transvaginal ultrasound shows a cervical length of 12 mm, which is consistent with preterm labor. A tocolytic and a single dose of betamethasone are administered. Betamethasone stimulates which fetal cells?"
    choices = ["Goblet cells", "Bronchial epithelial cells", "Type II pneumocytes", "Vascular smooth myocytes"]  # Type II pneumocytes

    res = await dria.execute(
        Task(
            workflow=web_multi_choice.workflow(question=question, choices=choices).model_dump(),
            models=[Model.QWEN2_5_7B_FP16],
        ),
        timeout=200,
    )
    return web_multi_choice.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
```

Expected output

```json
{
   "answer":"Answer: Based on the provided information and the analysis, the most likely correct answer is:  **Type II pneumocytes**  ### Detailed Reasoning: 1. **Medical Context and Purpose of Betamethasone:**    - Betamethasone is a corticosteroid used to accelerate fetal lung maturity in response to preterm labor.    - The primary goal is to reduce the risk of neonatal respiratory distress syndrome (RDS) by promoting surfactant production.  2. **Fetal Cells Targeted by Betamethasone:**    - The reference materials and analyses clearly indicate that betamethasone stimulates the production of pulmonary surfactant in the fetal lungs.    - Surfactant is primarily produced by type II pneumocytes (also known as type II alveolar cells).  3. **Relevant Analyses:**    - The provided context mentions that 'Betamethasone is a corticosteroid that is often used in obstetric practice to promote lung maturity in the fetus, thereby reducing neonatal morbidity and mortality associated with preterm birth.'    - It further states that betamethasone stimulates the synthesis of surfactant by the fetal lungs.    - The key point is that it 'primarily stimulates the production of surfactant by type II alveolar cells in the fetal lungs.'  4. **Elimination of Other Options:**    - **Goblet cells:** These are found in various parts of the respiratory tract, including the bronchi and trachea, but not specifically involved in surfactant production.    - **Bronchial epithelial cells:** While these cells line the airways, they are not primarily responsible for surfactant production.    - **Vascular smooth myocytes:** These are muscle cells found in blood vessel walls and are not related to lung function or surfactant production.  ### Conclusion: Given that betamethasone is specifically used to promote lung maturity by stimulating the production of pulmonary surfactant, which is a critical function performed by type II pneumocytes, the most likely correct option among those provided is **Type II pneumocytes**.",
   "model":"qwen2.5:7b-instruct-fp16"
}
```
