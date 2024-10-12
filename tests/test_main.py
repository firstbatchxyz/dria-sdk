import os
import asyncio
from dria.factory import TextRetrieval
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    text_retrieval = TextRetrieval()
    res = await dria.execute(
        Task(
            workflow=text_retrieval.workflow(
                task_description="Generate a text retrieval example for a science topic",
                query_type="informational",
                query_length="short",
                clarity="clear",
                num_words=100,
                language="English",
                difficulty="high school",
            ).model_dump(),
            models=[Model.LLAMA3_1_8B_FP16],
        ),
        timeout=45,
    )
    return text_retrieval.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
