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


class Model(str, Enum):
    # Ollama models
    NOUS_THETA = "finalend/hermes-3-llama-3.1:8b-q8_0"
    PHI3_MEDIUM = "phi3:14b-medium-4k-instruct-q4_1"
    PHI3_MEDIUM_128K = "phi3:14b-medium-128k-instruct-q4_1"
    PHI3_5_MINI_OL = "phi3.5:3.8b"
    PHI3_5_MINI_FP16 = "phi3.5:3.8b-mini-instruct-fp16"
    GEMMA2_9B_OL = "gemma2:9b-instruct-q8_0"
    GEMMA2_9B_FP16 = "gemma2:9b-instruct-fp16"
    LLAMA3_1 = "llama3.1:latest"
    LLAMA3_1_8BQ8 = "llama3.1:8b-instruct-q8_0"
    LLAMA3_1_8B_FP16 = "llama3.1:8b-instruct-fp16"
    LLAMA3_1_70B_OL = "llama3.1:70b-instruct-q4_0"
    LLAMA3_1_70BQ8 = "llama3.1:70b-instruct-q8_0"
    LLAMA3_2_1B = "llama3.2:1b"
    LLAMA3_2_3B = "llama3.2:3b"
    LLAMA3_3_70B = "llama3.3:70b"
    LLAMA3_1_8BTextQ4KM = "llama3.1:8b-text-q4_K_M"
    LLAMA3_1_8BTextQ8 = "llama3.1:8b-text-q8_0"
    LLAMA3_1_70BTextQ4KM = "llama3.1:70b-text-q4_0"
    LLAMA3_2_1BTextQ4KM = "llama3.2:1b-text-q4_K_M"
    QWEN_QWQ_OL = "qwq"
    QWEN_QWQ_OR = "qwen/qwq-32b-preview"
    QWEN2_5_7B_OL = "qwen2.5:7b-instruct-q5_0"
    QWEN2_5_7B_FP16 = "qwen2.5:7b-instruct-fp16"
    QWEN2_5_32B_FP16 = "qwen2.5:32b-instruct-fp16"
    QWEN2_5_CODER_1_5B = "qwen2.5-coder:1.5b"
    QWEN2_5_CODER_7B_OL = "qwen2.5-coder:7b"
    QWEN2_5_CODER_7B_Q8 = "qwen2.5-coder:7b-instruct-q8_0"
    QWEN2_5_CODER_7B_FP16 = "qwen2.5-coder:7b-instruct-fp16"
    DEEPSEEK_CODER_6_7B = "deepseek-coder:6.7b"
    MIXTRAL_8_7B = "mixtral:8x7b"

    DEEPSEEK_CHAT_OR = "deepseek/deepseek-chat"
    LLAMA_3_1_8B_OR = "meta-llama/llama-3.1-8b-instruct"
    LLAMA_3_1_70B_OR = "meta-llama/llama-3.1-70b-instruct"
    LLAMA_3_1_405B_OR = "meta-llama/llama-3.1-405b-instruct"
    LLAMA_3_1_70B_OR_F = "meta-llama/llama-3.1-70b-instruct:free"
    LLAMA_3_3_70B_OR = "meta-llama/llama-3.3-70b-instruct"
    ANTHROPIC_SONNET_3_5_OR = "anthropic/claude-3.5-sonnet:beta"
    ANTHROPIC_HAIKU_3_5_OR = "anthropic/claude-3-5-haiku-20241022:beta"
    QWEN2_5_72B_OR = "qwen/qwen-2.5-72b-instruct"
    QWEN2_5_7B_OR = "qwen/qwen-2.5-7b-instruct"
    QWEN2_5_CODER_32B_OR = "qwen/qwen-2.5-coder-32b-instruct"
    QWEN2_5_EVA_32B_OR = "eva-unit-01/eva-qwen-2.5-32b"
    DEEPSEEK_2_5_OR = "deepseek/deepseek-chat"
    NOUS_HERMES_405B_OR = "nousresearch/hermes-3-llama-3.1-405b"
    DEEPSEEK_R1_70B_OR = "deepseek/deepseek-r1-distill-llama-70b"
    DEEPSEEK_R1_OR = "deepseek/deepseek-r1"
    DEEPSEEK_R1_1_5B = "deepseek-r1:1.5b"
    DEEPSEEK_R1_7B = "deepseek-r1:7b"
    DEEPSEEK_R1_8B = "deepseek-r1:8b"
    DEEPSEEK_R1_14B = "deepseek-r1:14b"
    DEEPSEEK_R1_32B = "deepseek-r1:32b"
    DEEPSEEK_R1_70B = "deepseek-r1:70b"
    DEEPSEEK_R1 = "deepseek-r1"

    # Gemini models
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"
    GEMINI_20_FLASH = "gemini-2.0-flash-exp"
    GEMINI_10_PRO = "gemini-1.0-pro"
    GEMMA_2_2B_IT = "gemma-2-2b-it"
    GEMMA_2_9B_IT = "gemma-2-9b-it"
    GEMMA_2_27B_IT = "gemma-2-27b-it"

    # OpenAI models
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"

    # Providers
    OLLAMA = "ollama"
    OPENAI = "openai"
    CODER = "coder"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    SMALL = "small"
    MID = "mid"
    LARGE = "large"
    REASONING = "reasoning"

    @classmethod
    def default(cls):
        return cls.PHI3_5_MINI_OL


class SmallModels(Enum):
    NOUS_THETA = Model.NOUS_THETA.value
    PHI3_MEDIUM = Model.PHI3_MEDIUM.value
    PHI3_MEDIUM_128K = Model.PHI3_MEDIUM_128K.value
    PHI3_5_MINI_OL = Model.PHI3_5_MINI_OL.value
    PHI3_5_MINI_FP16 = Model.PHI3_5_MINI_FP16.value
    GEMMA2_9B_OL = Model.GEMMA2_9B_OL.value
    GEMMA2_9B_FP16 = Model.GEMMA2_9B_FP16.value
    LLAMA3_1 = Model.LLAMA3_1.value
    LLAMA3_1_8BQ8 = Model.LLAMA3_1_8BQ8.value
    LLAMA3_1_8B_FP16 = Model.LLAMA3_1_8B_FP16.value
    LLAMA3_2_1B = Model.LLAMA3_2_1B.value
    LLAMA3_2_3B = Model.LLAMA3_2_3B.value
    QWEN2_5_7B_OL = Model.QWEN2_5_7B_OL.value
    QWEN2_5_7B_FP16 = Model.QWEN2_5_7B_FP16.value
    DEEPSEEK_CHAT_OR = Model.DEEPSEEK_CHAT_OR.value
    LLAMA_3_1_8B_OR = Model.LLAMA_3_1_8B_OR.value
    QWEN2_5_7B_OR = Model.QWEN2_5_7B_OR.value
    DEEPSEEK_2_5_OR = Model.DEEPSEEK_2_5_OR.value
    GEMMA_2_2B_IT = Model.GEMMA_2_2B_IT.value
    GEMMA_2_9B_IT = Model.GEMMA_2_9B_IT.value
    GEMMA_2_27B_IT = Model.GEMMA_2_27B_IT.value


class MidModels(Enum):
    LLAMA3_1_70B_OL = Model.LLAMA3_1_70B_OL.value
    LLAMA3_1_70BQ8 = Model.LLAMA3_1_70BQ8.value
    QWEN2_5_32B_FP16 = Model.QWEN2_5_32B_FP16.value
    MIXTRAL_8_7B = Model.MIXTRAL_8_7B.value
    LLAMA_3_1_70B_OR = Model.LLAMA_3_1_70B_OR.value
    LLAMA_3_1_70B_OR_F = Model.LLAMA_3_1_70B_OR_F.value
    LLAMA_3_3_70B_OR = Model.LLAMA_3_3_70B_OR.value
    LLAMA3_3_70B = Model.LLAMA3_3_70B.value
    QWEN2_5_72B_OR = Model.QWEN2_5_72B_OR.value
    QWEN2_5_EVA_32B_OR = Model.QWEN2_5_EVA_32B_OR.value
    GEMINI_15_FLASH = Model.GEMINI_15_FLASH.value
    GEMINI_20_FLASH = Model.GEMINI_20_FLASH.value
    GEMINI_10_PRO = Model.GEMINI_10_PRO.value
    GPT4O_MINI = Model.GPT4O_MINI.value


class LargeModels(Enum):
    DEEPSEEK_R1_1_5B = Model.DEEPSEEK_R1_1_5B.value
    DEEPSEEK_R1_7B = Model.DEEPSEEK_R1_7B.value
    DEEPSEEK_R1_8B = Model.DEEPSEEK_R1_8B.value
    DEEPSEEK_R1_14B = Model.DEEPSEEK_R1_14B.value
    DEEPSEEK_R1_32B = Model.DEEPSEEK_R1_32B.value
    DEEPSEEK_R1_70B = Model.DEEPSEEK_R1_70B.value
    QWEN_QWQ_OL = Model.QWEN_QWQ_OL.value
    QWEN_QWQ_OR = Model.QWEN_QWQ_OR.value
    LLAMA_3_1_405B_OR = Model.LLAMA_3_1_405B_OR.value
    ANTHROPIC_SONNET_3_5_OR = Model.ANTHROPIC_SONNET_3_5_OR.value
    ANTHROPIC_HAIKU_3_5_OR = Model.ANTHROPIC_HAIKU_3_5_OR.value
    NOUS_HERMES_405B_OR = Model.NOUS_HERMES_405B_OR.value
    GEMINI_15_PRO = Model.GEMINI_15_PRO.value
    GPT4_TURBO = Model.GPT4_TURBO.value
    GPT4O = Model.GPT4O.value


class FunctionCallingModels(Enum):
    NOUS_THETA = Model.NOUS_THETA.value
    PHI3_MEDIUM = Model.PHI3_MEDIUM.value
    PHI3_MEDIUM_128K = Model.PHI3_MEDIUM_128K.value
    PHI3_5_MINI_FP16 = Model.PHI3_5_MINI_FP16.value
    GEMMA2_9B_OL = Model.GEMMA2_9B_OL.value
    GEMMA2_9B_FP16 = Model.GEMMA2_9B_FP16.value
    LLAMA3_1 = Model.LLAMA3_1.value
    LLAMA3_1_8BQ8 = Model.LLAMA3_1_8BQ8.value
    LLAMA3_1_8B_FP16 = Model.LLAMA3_1_8B_FP16.value
    LLAMA3_1_70B_OL = Model.LLAMA3_1_70B_OL.value
    LLAMA3_3_70B = Model.LLAMA3_3_70B.value
    LLAMA3_1_70BQ8 = Model.LLAMA3_1_70BQ8.value
    QWEN2_5_7B_OL = Model.QWEN2_5_7B_OL.value
    QWEN2_5_7B_FP16 = Model.QWEN2_5_7B_FP16.value
    QWEN2_5_32B_FP16 = Model.QWEN2_5_32B_FP16.value
    QWEN_QWQ_OL = Model.QWEN_QWQ_OL.value
    QWEN_QWQ_OR = Model.QWEN_QWQ_OR.value
    MIXTRAL_8_7B = Model.MIXTRAL_8_7B.value
    GPT4_TURBO = Model.GPT4_TURBO.value
    GPT4O = Model.GPT4O.value
    GPT4O_MINI = Model.GPT4O_MINI.value
    GEMINI_15_PRO = Model.GEMINI_15_PRO.value
    GEMINI_15_FLASH = Model.GEMINI_15_FLASH.value
    GEMINI_20_FLASH = Model.GEMINI_20_FLASH.value
    DEEPSEEK_CHAT_OR = Model.DEEPSEEK_CHAT_OR.value
    LLAMA_3_1_8B_OR = Model.LLAMA_3_1_8B_OR.value
    LLAMA_3_1_70B_OR = Model.LLAMA_3_1_70B_OR.value
    LLAMA_3_3_70B_OR = Model.LLAMA_3_3_70B_OR.value
    LLAMA_3_1_405B_OR = Model.LLAMA_3_1_405B_OR.value
    LLAMA_3_1_70B_OR_F = Model.LLAMA_3_1_70B_OR_F.value
    ANTHROPIC_SONNET_3_5_OR = Model.ANTHROPIC_SONNET_3_5_OR.value
    ANTHROPIC_HAIKU_3_5_OR = Model.ANTHROPIC_HAIKU_3_5_OR.value
    QWEN2_5_72B_OR = Model.QWEN2_5_72B_OR.value


class OpenAIModels(Enum):
    O1_MINI = Model.O1_MINI.value
    O1_PREVIEW = Model.O1_PREVIEW.value
    GPT4O = Model.GPT4O.value
    GPT4O_MINI = Model.GPT4O_MINI.value
    GPT4_TURBO = Model.GPT4_TURBO.value


class GeminiModels(Enum):
    GEMINI_15_PRO = Model.GEMINI_15_PRO.value
    GEMINI_15_FLASH = Model.GEMINI_15_FLASH.value
    GEMINI_20_FLASH = Model.GEMINI_20_FLASH.value
    GEMINI_10_PRO = Model.GEMINI_10_PRO.value
    GEMMA_2_2B_IT = Model.GEMMA_2_2B_IT.value
    GEMMA_2_9B_IT = Model.GEMMA_2_9B_IT.value
    GEMMA_2_27B_IT = Model.GEMMA_2_27B_IT.value


class OllamaModels(Enum):
    NOUS_THETA = Model.NOUS_THETA.value
    PHI3_MEDIUM = Model.PHI3_MEDIUM.value
    PHI3_MEDIUM_128K = Model.PHI3_MEDIUM_128K.value
    PHI3_5_MINI_OL = Model.PHI3_5_MINI_OL.value
    PHI3_5_MINI_FP16 = Model.PHI3_5_MINI_FP16.value
    GEMMA2_9B_OL = Model.GEMMA2_9B_OL.value
    GEMMA2_9B_FP16 = Model.GEMMA2_9B_FP16.value
    LLAMA3_1 = Model.LLAMA3_1.value
    LLAMA3_1_8BQ8 = Model.LLAMA3_1_8BQ8.value
    LLAMA3_1_8B_FP16 = Model.LLAMA3_1_8B_FP16.value
    LLAMA3_1_70B_OL = Model.LLAMA3_1_70B_OL.value
    LLAMA3_3_70B = Model.LLAMA3_3_70B.value
    LLAMA3_1_70BQ8 = Model.LLAMA3_1_70BQ8.value
    LLAMA3_2_1B = Model.LLAMA3_2_1B.value
    LLAMA3_2_3B = Model.LLAMA3_2_3B.value
    QWEN2_5_7B_OL = Model.QWEN2_5_7B_OL.value
    QWEN2_5_7B_FP16 = Model.QWEN2_5_7B_FP16.value
    QWEN2_5_32B_FP16 = Model.QWEN2_5_32B_FP16.value
    QWEN_QWQ_OL = Model.QWEN_QWQ_OL.value
    MIXTRAL_8_7B = Model.MIXTRAL_8_7B.value


class CoderModels(Enum):
    QWEN2_5_CODER_1_5B = Model.QWEN2_5_CODER_1_5B.value
    DEEPSEEK_CODER_6_7B = Model.DEEPSEEK_CODER_6_7B.value
    QWEN2_5_CODER_7B_OL = Model.QWEN2_5_CODER_7B_OL.value
    QWEN2_5_CODER_7B_Q8 = Model.QWEN2_5_CODER_7B_Q8.value
    QWEN2_5_CODER_7B_FP16 = Model.QWEN2_5_CODER_7B_Q8.value
    QWEN2_5_CODER_32B_OR = Model.QWEN2_5_CODER_32B_OR.value


class ReasoningModels(Enum):
    DEEPSEEK_R1_1_5B = Model.DEEPSEEK_R1_1_5B.value
    DEEPSEEK_R1_7B = Model.DEEPSEEK_R1_7B.value
    DEEPSEEK_R1_8B = Model.DEEPSEEK_R1_8B.value
    DEEPSEEK_R1_14B = Model.DEEPSEEK_R1_14B.value
    DEEPSEEK_R1_32B = Model.DEEPSEEK_R1_32B.value
    DEEPSEEK_R1_70B = Model.DEEPSEEK_R1_70B.value
    O1_MINI = Model.O1_MINI.value
    O1_PREVIEW = Model.O1_PREVIEW.value


class OpenRouterModels(Enum):
    DEEPSEEK_CHAT_OR = Model.DEEPSEEK_CHAT_OR.value
    LLAMA_3_1_8B_OR = Model.LLAMA_3_1_8B_OR.value
    LLAMA_3_1_70B_OR = Model.LLAMA_3_1_70B_OR.value
    LLAMA_3_3_70B_OR = Model.LLAMA_3_3_70B_OR.value
    LLAMA_3_1_70B_OR_F = Model.LLAMA_3_1_70B_OR_F.value
    ANTHROPIC_SONNET_3_5_OR = Model.ANTHROPIC_SONNET_3_5_OR.value
    ANTHROPIC_HAIKU_3_5_OR = Model.ANTHROPIC_HAIKU_3_5_OR.value
    QWEN2_5_72B_OR = Model.QWEN2_5_72B_OR.value
    QWEN2_5_7B_OR = Model.QWEN2_5_7B_OR.value
    QWEN2_5_EVA_32B_OR = Model.QWEN2_5_EVA_32B_OR.value
    DEEPSEEK_2_5_OR = Model.DEEPSEEK_2_5_OR.value
    QWEN_QWQ_OR = Model.QWEN_QWQ_OR.value
