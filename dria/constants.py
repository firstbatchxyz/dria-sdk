import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

INPUT_CONTENT_TOPIC: Final[str] = "task"
OUTPUT_CONTENT_TOPIC: Final[str] = "results"

RETURN_DEADLINE: Final[int] = 86400  # 24 hours in seconds
MONITORING_INTERVAL: Final[int] = 5  # 1 seconds
TASK_DEADLINE: Final[int] = 300
FETCH_INTERVAL: Final[int] = 1
FETCH_DEADLINE: Final[int] = 300
TASK_TIMEOUT: Final[int] = 300

MAX_OLLAMA_QUEUE: Final[int] = 3
MAX_API_QUEUE: Final[int] = 50

MAX_RETRIES_FOR_AVAILABILITY: Final[int] = 10

RPC_BASE_URL: Final[str] = "https://pro.rpc.dria.co"
RPC_BASE_URL_COMMUNITY: Final[str] = "https://community.rpc.dria.co"
SCORING_BATCH_SIZE = 50
COMPUTE_NODE_BATCH_SIZE = 5

HEARTBEAT_TOPIC: Final[str] = "ping"
HEARTBEAT_OUTPUT_TOPIC: Final[str] = "pong"

JINA_TOKEN: Final[str | None] = os.getenv("JINA_TOKEN")

LOG_LEVEL: Final[str | None] = os.getenv("LOG_LEVEL")

if not all(
    [
        INPUT_CONTENT_TOPIC,
        OUTPUT_CONTENT_TOPIC,
        RPC_BASE_URL,
        HEARTBEAT_TOPIC,
        HEARTBEAT_OUTPUT_TOPIC,
        RPC_BASE_URL_COMMUNITY,
    ]
):
    raise ValueError("One or more required constants are not set")
