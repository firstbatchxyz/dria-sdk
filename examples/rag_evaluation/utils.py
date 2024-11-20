from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    total: int = Field(...)
    correct: int = Field(...)
    correct_percentage: float = Field(...)
    partially_correct: int = Field(...)
    partially_correct_percentage: float = Field(...)
    incorrect: int = Field(...)
    incorrect_percentage: float = Field(...)


def calculate_accuracy(data) -> EvaluationResult:
    # Initialize counters
    total = len(data)
    correct = 0
    partially_correct = 0
    incorrect = 0

    # Count each type of evaluation
    for item in data:
        evaluation = item["evaluation"].lower()
        if evaluation == "correct":
            correct += 1
        elif evaluation == "partially correct":
            partially_correct += 1
        elif evaluation == "incorrect":
            incorrect += 1

    # Calculate percentages
    correct_percentage = (correct / total) * 100
    partially_correct_percentage = (partially_correct / total) * 100
    incorrect_percentage = (incorrect / total) * 100

    return EvaluationResult(
        total=total,
        correct=correct,
        correct_percentage=correct_percentage,
        partially_correct=partially_correct,
        partially_correct_percentage=partially_correct_percentage,
        incorrect=incorrect,
        incorrect_percentage=incorrect_percentage,
    )
