import os
import asyncio
from dria.factory import WebSearch
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    web_search = WebSearch()
    res = await dria.execute(
        Task(
            workflow=web_search.workflow(
                topic="Solomonoff Induction", mode="NARROW"
            ).model_dump(),
            models=[Model.LLAMA3_1_8B_FP16],
        ),
        timeout=200,
    )
    return web_search.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
