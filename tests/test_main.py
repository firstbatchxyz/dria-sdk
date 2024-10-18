import os
import asyncio
from dria.factory import GenerateCode
from dria.client import Dria
from dria.models import Task, Model

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])


async def evaluate():
    generate_code = GenerateCode()
    res = await dria.execute(
        Task(
            workflow=generate_code.workflow(
                instruction="Write a function to calculate the factorial of a number",
                language="python",
            ).model_dump(),
            models=[Model.QWEN2_5_CODER_7B_FP16],
        ),
        timeout=45,
    )
    return generate_code.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()
