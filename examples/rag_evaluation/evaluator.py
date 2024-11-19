import instructor
from pydantic import BaseModel, Field
from openai import OpenAI


class EvaluationResult(BaseModel):
    evaluation: str = Field(...)
    reasoning: str = Field(...)


class Evaluator:
    def __init__(self):
        self.client = instructor.from_openai(OpenAI())

    def evaluate(
        self, question: str, context: str, prediction: str, ground_truth: str
    ) -> EvaluationResult:

        return self.client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            response_model=EvaluationResult,
            messages=[
                {
                    "role": "system",
                    "content": "You are a world class judge to evaluate predicted answers to given question and context.",
                },
                {"role": "user", "content": f"{context}"},
                {"role": "user", "content": f"Question: {question}"},
                {"role": "user", "content": f"Prediction: {prediction}"},
                {"role": "user", "content": f"Ground truth: {ground_truth}"},
            ],
        )
