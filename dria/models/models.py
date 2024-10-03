from typing import List, Dict, Any, Optional

from dria_workflows import OpenAIParser, NousParser, LlamaParser

from pydantic import BaseModel, Field

from dria.models import Model

class P2PMessage(BaseModel):
    payload: str
    topic: str
    version: str
    timestamp: int


class NodeModel(BaseModel):
    uuid: str
    nodes: List[str]


class TaskInputModel(BaseModel):
    workflow: Dict[str, Any]
    model: List[str]


class TaskModel(BaseModel):
    taskId: str
    filter: Dict[str, Any]
    input: Dict[str, Any]
    deadline: int
    publicKey: str


class Task(BaseModel):
    workflow: Dict[str, Any]
    models: List[str]
    id: Optional[str] = None
    pipeline_id: str = ""
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    deadline: int = 0
    nodes: List[str] = []
    step_name: str = ""

    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow": self.workflow,
            "models": self.models,
            "pipeline_id": self.pipeline_id,
            "public_key": self.public_key,
            "private_key": self.private_key,
            "deadline": self.deadline,
            "nodes": self.nodes,
            "step_name": self.step_name
        }


class TaskResult(BaseModel):
    id: str
    task_input: Any
    step_name: str
    result: Any
    model: str

    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_input": self.task_input,
            "step_name": self.step_name,
            "result": self.result,
            "model": self.model
        }

    def parse(self):
        model_parsers = {
            Model.GPT4O: OpenAIParser(),
            Model.GPT4O_MINI: OpenAIParser(),
            Model.GPT4_TURBO: OpenAIParser(),
            Model.QWEN2_5_32B_FP16: OpenAIParser(),
            Model.QWEN2_5_7B: OpenAIParser(),
            Model.QWEN2_5_7B_FP16: OpenAIParser(),
            Model.GEMMA2_9B: OpenAIParser(),
            Model.GEMMA2_9B_FP16: OpenAIParser(),
            Model.PHI3_5_MINI_FP16: OpenAIParser(),
            Model.PHI3_MEDIUM: OpenAIParser(),
            Model.PHI3_MEDIUM_128K: OpenAIParser(),
            Model.MIXTRAL_8_7B: OpenAIParser(),
            Model.LLAMA3_1_8B_FP16: LlamaParser(),
            Model.LLAMA3_1_70B: LlamaParser(),
            Model.LLAMA3_1_70BQ8: LlamaParser(),
            Model.LLAMA3_2_1B: LlamaParser(),
            Model.LLAMA3_2_3B: LlamaParser(),
            Model.LLAMA3_1_8BQ8: LlamaParser(),
            Model.NOUS_THETA: NousParser(),
        }

        parser = model_parsers.get(Model(self.model))
        if parser:
            return parser.parse(self.result)
        else:
            raise ValueError(f"Model {self.model} not supported function calling")




class TaskInput(BaseModel):
    class Config:
        extra = "allow"

    def __init__(self, **data: Any):
        super().__init__(**data)
        for key, value in data.items():
            if key not in self.__fields__:
                self.__fields__[key] = Field(default=value)
                setattr(self, key, value)
