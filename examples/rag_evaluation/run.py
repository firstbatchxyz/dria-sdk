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
        [Model.GPT4O_MINI, Model.LLAMA3_1_70B, Model.QWEN2_5_32B_FP16, Model.GPT4O]
    )
    executor.load_instructions(
        [{"chunks": random.sample(file_chunks, 3)} for _ in range(20)]
    )
    return await executor.run()


def main():

    # Load dataset
    dataset = load_dataset("m-ric/huggingface_doc")
    eval_chunks = dataset["train"].select(range(int(0.10 * len(dataset["train"]))))
    eval_chunks = [chunk["text"] for chunk in eval_chunks]
    # Create synthetic evaluation data using %10 of the dataset
    dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])
    qa_eval = asyncio.run(run_qa_pipeline(dria, eval_chunks))
    multihop_eval = asyncio.run(run_multihop_tasks(dria, eval_chunks))

    # Initialize RAG
    all_chunks = dataset["train"]
    all_chunks = [chunk["text"] for chunk in all_chunks]
    rag = RAG(all_chunks)

    answers = []
    evaluate = Evaluator()

    # Answer QA data
    for pair in tqdm(qa_eval):
        answer = rag.answer(pair["question"])
        answers.append(
            {
                "prediction": answer.get_answer(),
                "answer": pair["answer"],
                "type": "simple",
                "question": pair["question"],
            }
        )

    # Answer multi-hop QA data
    for pair in tqdm(multihop_eval):
        for hop_type in ["1-hop", "2-hop", "3-hop"]:
            answer = rag.answer(pair[hop_type])
            answers.append(
                {
                    "prediction": answer.get_answer(),
                    "answer": pair["answer"],
                    "type": hop_type,
                    "question": pair[hop_type],
                }
            )

    # Evaluate all answers
    evaluated_answers = []
    for answer in tqdm(answers):
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

    # Calculate accuracy

    accuracy = calculate_accuracy(evaluated_answers)
    print("**********")
    print(f"Total: {accuracy.total}")
    print(f"Correct: {accuracy.correct} ({accuracy.correct_percentage}%)")
    print(
        f"Partially correct: {accuracy.partially_correct} ({accuracy.partially_correct_percentage}%)"
    )
    print(f"Incorrect: {accuracy.incorrect} ({accuracy.incorrect_percentage}%)")
    print("**********")
