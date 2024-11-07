from typing import List, Optional, Dict, Any
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from pydantic import BaseModel, Field, model_validator, ValidationInfo
from openai import OpenAI
import instructor
from pathlib import Path
import re
import os
from collections import defaultdict
from dria.client import Dria
from dria.factory import QAPipeline
from dria.pipelines import PipelineConfig
from dria.factory import MultiHopQuestion
from dria.models import Model
from dria.batches import ParallelSingletonExecutor
import json
import random
from tqdm import tqdm
import asyncio


class ReadmeChunker:
    """A class to chunk markdown files based on headers."""

    def __init__(self, docs_dir: str, min_chunk_size: int = 500):
        """
        Initialize the ReadmeChunker.

        Args:
            docs_dir (str): Directory containing markdown files
            min_chunk_size (int): Minimum size of chunks in characters
        """
        self.docs_dir = Path(docs_dir)
        self.min_chunk_size = min_chunk_size
        self.chunks = self._process_markdown_files()

    def _process_markdown_files(self) -> List[dict]:
        """Process all markdown files in the directory."""
        all_chunks = []

        try:
            for file_path in self.docs_dir.rglob("*.md"):
                chunks = self._process_single_file(file_path)
                all_chunks.extend(chunks)

            return all_chunks

        except Exception as e:
            raise Exception(f"Error processing markdown files: {str(e)}")

    def _process_single_file(self, file_path: Path) -> List[dict]:
        """
        Process a single markdown file.

        Args:
            file_path (Path): Path to the markdown file

        Returns:
            List[str]: List of chunks from the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                return [
                    {"chunk": ch, "path": file_path}
                    for ch in self._chunk_by_headers(content)
                ]

        except Exception as e:
            print(f"Warning: Could not process {file_path}: {str(e)}")
            return []

    def _chunk_by_headers(self, markdown_text: str) -> List[str]:
        """
        Split markdown text into chunks based on headers.

        Args:
            markdown_text (str): The markdown text to chunk

        Returns:
            List[str]: List of text chunks
        """
        header_pattern = r"^#{1,6}\s.*$"
        chunks = []
        current_chunk = []
        current_size = 0

        for line in markdown_text.split("\n"):
            if re.match(header_pattern, line) and current_size > self.min_chunk_size:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = len(line)
            else:
                current_chunk.append(line)
                current_size += len(line) + 1

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def get_chunks(self):
        return self.chunks

    def get_files(self):
        chunks = self.get_chunks()
        files = defaultdict(list)
        for chunk in chunks:
            files[str(chunk["path"])].append(chunk["chunk"])
        return files


class VectorStore:
    """A class to manage vector storage and similarity search operations."""

    def __init__(self, embedding_model: Optional[Any] = None):
        """
        Initialize the VectorStore.

        Args:
            embedding_model: The embedding model to use (defaults to OpenAIEmbeddings)
        """
        self.embedding_model = embedding_model or OpenAIEmbeddings(
            api_key=os.environ["OPENAI_API_KEY"]
        )
        self.vector_store = InMemoryVectorStore(self.embedding_model)

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.

        Args:
            documents (List[Document]): List of Document objects to add
        """
        try:
            self.vector_store.add_documents(documents)
        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")

    def similarity_search(
        self, query: str, k: int = 1, filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform similarity search on the vector store.

        Args:
            query (str): The search query
            k (int): Number of results to return
            filter (Dict): Optional metadata filter

        Returns:
            List[Document]: List of similar documents
        """
        if self.vector_store is None:
            raise ValueError("Vector store is empty. Add documents first.")

        try:
            if filter:
                results = self.vector_store.similarity_search(
                    query=query, k=k, filter=filter
                )
            else:
                results = self.vector_store.similarity_search(query=query, k=k)
            return results

        except Exception as e:
            raise Exception(f"Error performing similarity search: {str(e)}")


# https://python.useinstructor.com/examples/exact_citations/#validation-method-validate_sources


class Fact(BaseModel):
    fact: str = Field(...)
    substring_quote: List[str] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self, info: ValidationInfo) -> "Fact":
        text_chunks = info.context.get("text_chunk", None)
        spans = list(self.get_spans(text_chunks))
        self.substring_quote = [text_chunks[span[0] : span[1]] for span in spans]
        return self

    def get_spans(self, context):
        for quote in self.substring_quote:
            yield from self._get_span(quote, context)

    @staticmethod
    def _get_span(quote, context):
        for match in re.finditer(re.escape(quote), context):
            yield match.span()


class QuestionAnswer(BaseModel):
    question: str = Field(...)
    answer: List[Fact] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self) -> "QuestionAnswer":
        self.answer = [fact for fact in self.answer if len(fact.substring_quote) > 0]
        return self


class NaiveRAG:
    def __init__(self):
        self.chunker = ReadmeChunker("blog/docs")
        self.vectorstore = VectorStore()
        self.vectorstore.add_documents(
            [
                Document(
                    id=str(i),
                    page_content=chunk["chunk"],
                    metadata={"path": chunk["path"]},
                )
                for i, chunk in enumerate(self.chunker.get_chunks())
            ]
        )
        self.client = instructor.from_openai(OpenAI())

    def search(self, query: str, top_k=3):
        results = self.vectorstore.similarity_search(query=query, k=top_k)
        return [doc.page_content for doc in results]

    def answer(self, query: str, context: str) -> QuestionAnswer:
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            response_model=QuestionAnswer,
            messages=[
                {
                    "role": "system",
                    "content": "You are a world class algorithm to answer questions with correct and exact citations.",
                },
                {"role": "user", "content": f"{context}"},
                {"role": "user", "content": f"Question: {query}"},
            ],
            validation_context={"text_chunk": context},
        )


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
            model="gpt-4o-mini",
            temperature=0,
            response_model=EvaluationResult,
            messages=[
                {
                    "role": "system",
                    "content": "You are a world class algorithm to evaluate predicted questions.",
                },
                {"role": "user", "content": f"{context}"},
                {"role": "user", "content": f"Question: {question}"},
                {"role": "user", "content": f"Prediction: {prediction}"},
                {"role": "user", "content": f"Ground truth: {ground_truth}"},
            ],
        )


async def run_qa_pipeline(dria: Dria, chunker: ReadmeChunker):
    # read each chunk belonging to a file and merge them into a single string
    file_chunks = ["\n".join(v) for k, v in chunker.get_files().items()]
    print(f"num_files: {len(file_chunks)}")
    await dria.initialize()

    pipeline = QAPipeline(dria, config=PipelineConfig()).build(
        simulation_description="People from different background trying learn how to build an efficient RAG pipeline. Developers, developers in big corporations, bussiness that try to inplement RAG in to their custom docs, AI researchers.",
        num_samples=2,
        persona="A researcher that is concise and direct",
        chunks=file_chunks,
    )

    result = await pipeline.execute(return_output=True)
    with open("qa.json", "w") as f:
        json.dump(result, f, indent=4)


async def run_multihop_tasks(dria: Dria, chunker: ReadmeChunker):
    file_chunks = ["\n".join(v) for k, v in chunker.get_files().items()]
    singleton = MultiHopQuestion()
    executor = ParallelSingletonExecutor(dria, singleton)
    executor.set_timeout(150)
    executor.set_models(
        [Model.GPT4O_MINI, Model.GEMINI_15_FLASH, Model.QWEN2_5_32B_FP16, Model.GPT4O]
    )
    executor.load_instructions(
        [{"chunks": random.sample(file_chunks, 3)} for _ in range(20)]
    )
    results = await executor.run()
    with open("multihop_output.json", "w") as f:
        json.dump(results, f, indent=4)


def calculate_accuracy(data):
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

    # Print results
    print(f"Total evaluations: {total}")
    print(f"Correct: {correct} ({correct_percentage:.2f}%)")
    print(
        f"Partially Correct: {partially_correct} ({partially_correct_percentage:.2f}%)"
    )
    print(f"Incorrect: {incorrect} ({incorrect_percentage:.2f}%)")


def main():
    dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])
    chunker = ReadmeChunker("blog/docs")
    rag = NaiveRAG()
    asyncio.run(run_qa_pipeline(dria, chunker))
    asyncio.run(run_multihop_tasks(dria, chunker))

    answers = []
    evaluate = Evaluator()

    # Load QA data
    with open("qa.json", "r") as f:
        qa = json.loads(f.read())

    # Load MultiHop QA
    with open("multihop_output.json", "r") as f:
        multi_hop_qa = json.loads(f.read())

    # Process simple QA
    for pair in tqdm(qa):
        docs = rag.search(pair["question"])
        answer = rag.answer(pair["question"], "\n".join(docs))
        answers.append(
            {
                "prediction": answer,
                "answer": pair["answer"],
                "type": "simple",
                "question": pair["question"],
                "context": "\n".join(docs),
            }
        )

    # Process multi-hop QA
    for pair in tqdm(multi_hop_qa):
        for hop_type in ["1-hop", "2-hop", "3-hop"]:
            docs = rag.search(pair[hop_type])
            answer = rag.answer(pair[hop_type], "\n".join(docs))
            answers.append(
                {
                    "prediction": answer,
                    "answer": pair["answer"],
                    "type": hop_type,
                    "question": pair[hop_type],
                    "context": "\n".join(docs),
                }
            )

    # Evaluate all answers
    evaluated_answers = []
    for answer in tqdm(answers):
        result = evaluate.evaluate(
            answer["question"],
            answer["context"],
            answer["prediction"],
            answer["answer"],
        )
        evaluated_answers.append(
            {
                "question": answer["question"],
                "answer": answer["answer"],
                "prediction": "\n".join([f.fact for f in answer["prediction"].answer]),
                "evaluation": result.evaluation.lower(),
                "reasoning": result.reasoning,
            }
        )

    # Print evaluation results
    calculate_accuracy(evaluated_answers)
