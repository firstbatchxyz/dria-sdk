import warnings

warnings.filterwarnings("ignore", module="pydantic")
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
    workflow: Any
    model: List[str]


class TaskModel(BaseModel):
    taskId: str
    filter: Dict[str, Any]
    input: Dict[str, Any]
    pickedNodes: List
    deadline: int
    publicKey: str
    datasetId: str
    privateKey: str
    nodePeerIds: List[str]


class Task(BaseModel):
    workflow: Any
    models: List[Model]
    id: Optional[str] = None
    pipeline_id: str = ""
    dataset_id: Optional[str] = None
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    deadline: int = 0
    created_ts: int = 0
    filter: Dict = {}
    nodes: List[str] = []
    step_name: str = ""
    processed: bool = False

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow": self.workflow,
            "models": self.models,
            "pipeline_id": self.pipeline_id,
            "public_key": self.public_key,
            "private_key": self.private_key,
            "deadline": self.deadline,
            "nodes": self.nodes,
            "step_name": self.step_name,
            "created_ts": self.created_ts,
            "dataset_id": self.dataset_id,
        }


class TaskResult(BaseModel):
    id: str
    task_input: Any
    step_name: str
    result: Any
    model: str

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_input": self.task_input,
            "step_name": self.step_name,
            "result": self.result,
            "model": self.model,
        }

    def parse(self):
        model_parsers = {
            Model.GPT4O: OpenAIParser(),
            Model.GPT4O_MINI: OpenAIParser(),
            Model.GPT4_TURBO: OpenAIParser(),
            Model.QWEN2_5_32B_FP16: OpenAIParser(),
            Model.QWEN_QWQ: OpenAIParser(),
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
            Model.LLAMA3_3_70B: LlamaParser(),
            Model.LLAMA3_1_70BQ8: LlamaParser(),
            Model.LLAMA3_2_1B: LlamaParser(),
            Model.LLAMA3_2_3B: LlamaParser(),
            Model.LLAMA3_1_8BQ8: LlamaParser(),
            Model.NOUS_THETA: NousParser(),
            Model.GEMINI_15_PRO: OpenAIParser(),
            Model.GEMINI_15_FLASH: OpenAIParser(),
            Model.GEMINI_20_FLASH: OpenAIParser(),
        }

        parser = model_parsers.get(Model(self.model))
        if parser:
            return parser.parse(self.result)
        else:
            raise ValueError(f"Model {self.model} not supported function calling")


class TaskInput(BaseModel):
    class Config:
        extra = "allow"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            if key not in self.__fields__:
                self.__fields__[key] = Field(default=value)
                setattr(self, key, value)


class InputParam:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def __repr__(self):
        items = [f"{k}={v!r}" for k, v in self.__dict__.items()]
        return f"InputParam({', '.join(items)})"
