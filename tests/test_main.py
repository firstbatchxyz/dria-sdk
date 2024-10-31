import json
import os
from dria.factory import (
    StructRAGGraph,
    StructRAGCatalogue,
    StructRAGAlgorithm,
    StructRAGTable,
    StructRAGJudge,
    StructRAGSimulate,
    StructRAGAnswer,
    StructRAGExtract,
    StructRAGDecompose,
)
from dria.client import Dria
from dria.models import Model, Task
import asyncio
from context import c1,c2,c3

dria = Dria(rpc_token=os.environ["DRIA_RPC_TOKEN"])

async def evaluate():
    catalogue = StructRAGAnswer()
    algo = "**Information addressing the query:**\n\n* Diego Costa played for Spain during the 2018 FIFA World Cup.\n* His first goal against Portugal on June 15, 2018, was the first World Cup goal awarded based on a VAR decision.\n\nThe raw content does not explicitly state which club team Costa played for at the time, but it does mention he was included in Spain's squad by manager Vicente del Bosque in 2014 while playing at the Vicente Calderón Stadium, his club ground at the time. This suggests he played for Atlético Madrid then. However, the query specifically asks about his club during the 2018 World Cup where the VAR decision occurred.  More information is needed to definitively answer which club team he played for at that specific time."
    query = 'Diago Costa played for which club when he was awarded the first FIFA World Cup Goal based on a VAR Decision?'
    algo2 = "Diego Costa played for Atlético Madrid when he was awarded the first FIFA World Cup goal based on a VAR decision.  This information is implied by the mention of his former Atlético teammate Koke providing the assist for one of Costa's goals for Spain and the fact that the article focuses on Costa's international career with Spain during and after the 2014 World Cup."
    documents = [
        c1, c2, c3
    ]
    documents_info = [
        "Video_assistant_referee",
        "2018_FIFA_World_Cup#Officiating",
        "Diego_Costa#Spain"
    ]
    res = await dria.execute(
        Task(
            workflow=catalogue.workflow(question=query, sub_questions=[""], precise_knowledge=[algo, algo2]).model_dump(),
            models=[Model.GEMINI_15_PRO],
        ),
        timeout=45,
    )
    return catalogue.parse_result(res)


def main():
    result = asyncio.run(evaluate())
    print(result)


if __name__ == "__main__":
    main()



