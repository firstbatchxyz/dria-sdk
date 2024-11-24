import os
from dria.client import Dria
from dria.factory import QAPipeline
from dria.pipelines import PipelineConfig
from dria.factory import MultiHopQuestion
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
import random
from examples.rag_evaluation.evaluator import Evaluator
from examples.rag_evaluation.rag import RAG
from examples.rag_evaluation.utils import calculate_accuracy
from datasets import load_dataset
import asyncio
from tqdm import tqdm
import json


async def run_qa_pipeline(dria: Dria, file_chunks):
    await dria.initialize()

    pipeline = QAPipeline(dria, config=PipelineConfig()).build(
        simulation_description="AI developers and researchers learning Huggingface. "
        "Some focus on fine-tuning and post-training, others on RAG systems, "
        "retrieval problems, image models, or dataset work.",
        num_samples=1,
        persona="A HuggingFace expert that is concise and direct",
        chunks=file_chunks,
    )

    return await pipeline.execute(return_output=True)


async def run_multihop_tasks(dria: Dria, file_chunks):
    singleton = MultiHopQuestion()
    executor = ParallelSingletonExecutor(dria, singleton)
    executor.set_timeout(150)
    executor.set_models(
        [
            Model.QWEN2_5_72B_OR,
            Model.GEMINI_15_PRO,
            Model.GPT4O,
            Model.ANTHROPIC_SONNET_3_5_OR,
            Model.ANTHROPIC_HAIKU_3_5_OR,
        ]
    )
    executor.load_instructions(
        [{"chunks": random.sample(file_chunks, 3)} for _ in range(10)]
    )
    return await executor.run()


def main():
    # Load dataset
    dataset = load_dataset("m-ric/huggingface_doc")
    eval_chunks = dataset["train"].select(range(int(0.01 * len(dataset["train"]))))
    eval_chunks = [chunk["text"] for chunk in eval_chunks]

    # Create synthetic evaluation data using %1 of the dataset
    dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])
    qa_eval = asyncio.run(run_qa_pipeline(dria, eval_chunks))
    multihop_eval = asyncio.run(run_multihop_tasks(dria, eval_chunks))

    # Save evaluation data for inspection
    with open("qa_eval.json", "w") as f:
        f.write(json.dumps(qa_eval, indent=2))

    with open("multi_hop_qa_eval.json", "w") as f:
        f.write(json.dumps(multihop_eval, indent=2))

    # Initialize RAG
    all_chunks = dataset["train"]
    all_chunks = [chunk["text"] for chunk in all_chunks]
    rag = RAG(all_chunks)

    answers = {"qa": [], "1-hop": [], "2-hop": [], "3-hop": []}
    evaluate = Evaluator()

    # Answer QA data
    for pair in tqdm(qa_eval, desc="Answering QA"):
        answer = rag.answer(pair["question"])
        print("**** ", answer)
        answers["qa"].append(
            {
                "prediction": answer.get_answer(),
                "answer": pair["answer"],
                "type": "simple",
                "question": pair["question"],
            }
        )

    # Answer multi-hop QA data
    for pair in tqdm(multihop_eval, desc="Answering multi-hop QA"):
        for hop_type in ["1-hop", "2-hop", "3-hop"]:
            answer = rag.answer(pair[hop_type])
            answers[hop_type].append(
                {
                    "prediction": answer.get_answer(),
                    "answer": pair["answer"],
                    "type": hop_type,
                    "question": pair[hop_type],
                }
            )

    # Evaluate all answers
    for k, v in answers.items():
        evaluated_answers = []
        for answer in tqdm(v, desc="Evaluating answers"):
            result = evaluate.evaluate(
                answer["question"],
                answer["prediction"],
                answer["answer"],
            )
            evaluated_answers.append(
                {
                    "question": answer["question"],
                    "answer": answer["answer"],
                    "prediction": answer["prediction"],
                    "evaluation": result.evaluation.lower(),
                    "reasoning": result.reasoning,
                }
            )

        accuracy = calculate_accuracy(evaluated_answers)
        print(f"********** {k} accuracy")
        print(f"Total: {accuracy.total}")
        print(f"Correct: {accuracy.correct} ({accuracy.correct_percentage}%)")
        print(
            f"Partially correct: {accuracy.partially_correct} ({accuracy.partially_correct_percentage}%)"
        )
        print(f"Incorrect: {accuracy.incorrect} ({accuracy.incorrect_percentage}%)")
        print("**********")

        with open(f"evaluated_answers_{k}.json", "w") as f:
            f.write(json.dumps(evaluated_answers, indent=2))


if __name__ == "__main__":
    main()
