import os
import asyncio
from dria.factory import Simple
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    web_search = Simple()
    task = Task(
        workflow=web_search.workflow(
            prompt="What is Solomonoff Induction? Explain shortly."
        ).model_dump(),
        models=[Model.OLLAMA],
    )
    res = await dria.execute(
        task=[task] * 10,
        timeout=200,
    )
    return web_search.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
