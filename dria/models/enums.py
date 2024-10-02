from enum import Enum


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CallbackType(Enum):
    SCATTER = "scatter"
    BROADCAST = "broadcast"
    AGGREGATE = "aggregate"
    DEFAULT = "default"
    CUSTOM = "custom"


class Model(Enum):
    # Ollama models
    NOUS_THETA = "finalend/hermes-3-llama-3.1:8b-q8_0"
    PHI3_MEDIUM = "phi3:14b-medium-4k-instruct-q4_1"
    PHI3_MEDIUM_128K = "phi3:14b-medium-128k-instruct-q4_1"
    PHI3_5_MINI = "phi3.5:3.8b"
    PHI3_5_MINI_FP16 = "phi3.5:3.8b-mini-instruct-fp16"
    GEMMA2_9B = "gemma2:9b-instruct-q8_0"
    GEMMA2_9B_FP16 = "gemma2:9b-instruct-fp16"
    LLAMA3_1_8BQ8 = "llama3.1:8b-instruct-q8_0"
    LLAMA3_1_8B_FP16 = "llama3.1:8b-instruct-fp16"
    LLAMA3_1_70B = "llama3.1:70b-instruct-q4_0"
    LLAMA3_1_70BQ8 = "llama3.1:70b-instruct-q8_0"
    LLAMA3_2_1B = "llama3.2:1b"
    LLAMA3_2_3B = "llama3.2:3b"
    QWEN2_5_7B = "qwen2.5:7b-instruct-q5_0"
    QWEN2_5_7B_FP16 = "qwen2.5:7b-instruct-fp16"
    QWEN2_5_32B_FP16 = "qwen2.5:32b-instruct-fp16"
    QWEN2_5_CODER_1_5B = "qwen2.5-coder:1.5b"
    DEEPSEEK_CODER_6_7B = "deepseek-coder:6.7b"
    MIXTRAL_8_7B = "mixtral:8x7b"

    # OpenAI models
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"

    # As provider
    OLLAMA = "ollama"
    OPENAI = "openai"

    @classmethod
    def default(cls):
        return cls.PHI3_5_MINI


class PushStrategy(Enum):
    SINGLE = "single"  # Step output is directly pushed to the next step
    SEQUENTIAL = "sequential"  # Step output is processed in a loop, pushing new steps for each item
