import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

INPUT_CONTENT_TOPIC: Final[str] = "task"
RETURN_DEADLINE: Final[int] = 86400  # 24 hours in seconds
MONITORING_INTERVAL: Final[int] = 20  # 20 seconds
TASK_DEADLINE: Final[int] = 300
FETCH_INTERVAL: Final[int] = 2
MAX_OLLAMA_QUEUE: Final[int] = 3
MAX_API_QUEUE: Final[int] = 50
RPC_BASE_URL: Final[str] = "https://pro.rpc.dria.co"
RPC_BASE_URL_COMMUNITY: Final[str] = "http://3.238.84.83:8006"
SCORING_BATCH_SIZE = 50
COMPUTE_NODE_BATCH_SIZE = 5
HEARTBEAT_OUTPUT_TOPIC: Final[str] = "pong"
LOG_LEVEL: Final[str | None] = os.getenv("LOG_LEVEL")
