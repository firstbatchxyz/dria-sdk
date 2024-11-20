from typing import List, Union, Tuple
from pydantic import BaseModel, Field, ValidationInfo, model_validator
from openai import OpenAI
from ragatouille import RAGPretrainedModel
import instructor
import re


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

    def get_answer(self):
        return "\n".join([fact.fact for fact in self.answer])


class RAG:
    def __init__(self, chunks):
        self.rag = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
        self.index_path = self.rag.index(index_name="my_index", collection=chunks)
        self.client = instructor.from_openai(OpenAI())

    def search(
        self, questions: Union[List[str], str], top_k=3
    ) -> Union[List[List[str]], List[str]]:
        res = self.rag.search(questions)
        return [r[:top_k] for r in res]

    def answer(self, question: str) -> QuestionAnswer:

        docs = self.search(question)
        context = "\n".join(docs)

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
                {"role": "user", "content": f"Question: {question}"},
            ],
            validation_context={"text_chunk": context},
        )
