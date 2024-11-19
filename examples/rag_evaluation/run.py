import os
from dria.client import Dria
from dria.factory import QAPipeline
from dria.pipelines import PipelineConfig
from dria.factory import MultiHopQuestion
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
import random
from examples.rag_evaluation.chunker import ReadmeChunker
from examples.rag_evaluation.evaluator import Evaluator
from examples.rag_evaluation.rag import RAG
from examples.rag_evaluation.utils import calculate_accuracy
import asyncio
from tqdm import tqdm


async def run_qa_pipeline(dria: Dria, chunker: ReadmeChunker):
    # read each chunk belonging to a file and merge them into a single string
    file_chunks = chunker.get_files()
    print(f"num_files: {len(file_chunks)}")
    await dria.initialize()

    pipeline = QAPipeline(dria, config=PipelineConfig()).build(
        simulation_description="People from different background trying learn how to build an efficient RAG pipeline. Developers, developers in big corporations, bussiness that try to inplement RAG in to their custom docs, AI researchers.",
        num_samples=2,
        persona="A researcher that is concise and direct",
        chunks=file_chunks,
    )

    return await pipeline.execute(return_output=True)


async def run_multihop_tasks(dria: Dria, chunker: ReadmeChunker):
    file_chunks = chunker.get_files()
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
    dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])
    rag = RAG()
    qa_eval = asyncio.run(run_qa_pipeline(dria, rag.chunker))
    multihop_eval = asyncio.run(run_multihop_tasks(dria, rag.chunker))

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
    print(f"Partially correct: {accuracy.partially_correct} ({accuracy.partially_correct_percentage}%)")
    print(f"Incorrect: {accuracy.incorrect} ({accuracy.incorrect_percentage}%)")
    print("**********")


