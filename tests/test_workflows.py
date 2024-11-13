import pytest
import os
import asyncio
from dria.pipelines import PipelineConfig
from dria.client import Dria
from dria.factory import Simple, GenerateCode, MultiHopQuestion, CSVExtenderPipeline
from dria.models import Task, Model


# Setup fixture for Dria client
@pytest.fixture
def dria_client():
    token = os.getenv("DRIA_RPC_TOKEN")
    if not token:
        pytest.skip("DRIA_RPC_TOKEN environment variable not set")
    return Dria(rpc_token=token)


# Test data fixture for MultiHopQuestion
@pytest.fixture
def text_chunks():
    return [
        "In return for his loyalty to the new regime, de Ros received extensive royal patronage. This included lands, grants, wardships and the right to arrange the wards' marriages. De Ros performed valuable service as an advisor and ambassador (perhaps most importantly to Henry, who was often in a state of near-penury; de Ros was a wealthy man, and regularly loaned the crown large amounts of money). Important as he was in government and the regions, de Ros was unable to avoid the tumultuous regional conflicts and feuds which were rife at this time. In 1411 he was involved in a land dispute with a powerful Lincolnshire neighbour, and narrowly escaped an ambush; he sought and received redress in parliament. Partly because of de Ros's restraint in not seeking the severe penalties available to him, he was described by a 20th-century historian as a particularly wise and forbearing figure for his time.",
        """de Ros was an active royal official in the local administration and became a leading member of political society in the north Midlands and Yorkshire, where he regularly headed royal commissions.[49] He was frequently appointed a justice of the peace, particularly in Leicestershire.[50] De Ros's service to the crown was not confined to the regions; in 1401, he directed the king's attempts to increase the royal income. He was appointed Henry's negotiator with the House of Commons, to persuade the Commons to agree to a subsidy for the king's intended invasion of Scotland later that summer. De Ros and the Commons representatives met in Westminster's refectory. Emphasising "favourable consideration"[49] the Commons would receive from the king, he played heavily on the king's expenses in defending the Welsh and Scottish Marches.[49] Each party was wary of the other; the king did not wish to set a precedent, and the Commons were traditionally wary of the House of Lords.[51] Six years later, de Ros played much the same role—with the Duke of York and the Archbishop of Canterbury, on a committee hearing the Commons' complaints. The result of these discussions was an altercation in which the Commons, reports the parliament roll, were "hugely disturbed".[52] This disturbance, according to J. H. Wylie, was probably the result of something de Ros said[52] and would account for the Commons' reluctance to meet him or his committee. De Ros's remit was to persuade the Commons to grant as substantial a tax—in exchange for as few liberties granted—as possible.[53] An experienced parliamentarian, he attended most parliaments from 1394 to 1413.[20]""",
        """With his wife, Margaret Fitzalan, William de Ros had four sons:[127] John, Thomas, Robert and Richard. They also had four daughters: Beatrice, Alice, Margaret and Elizabeth.[128][note 19] De Ros also had an illegitimate son, John, by a now-unknown woman.[129] Charles de Ross suggests that he "provides full confirmation of what the scanty evidence as to the character of his earlier career suggests, that de Ros was a man of just and equitable temperament"[130] by the nature and extent of his bequests. His heir, John, inherited his father's lordship and patrimony and his armour and a gold sword. His third son, Robert—whom Ross describes as "evidently his favourite"[129]—also inherited a quantity of land.[129] De Ros made this provision for Robert from John's patrimony, a decision described by G. L. Harriss as "overrid[ing] both family duty and convention".[127] His younger three sons (Thomas, Robert, and Richard) received a third of de Ros's goods among them; Thomas, traditional for a younger son, was intended for an ecclesiastical career. Margaret received another third of his goods. His illegitimate son, John, received £40 towards his upkeep. Loyal retainers received benefices, and de Ros's "humbler dependents"—for instance, the poor on his Lincolnshire estates—received often-massive sums among them.[note 20] His executors—one of whom was his heir, John—received £20 each for their services.[119] De Ros was buried in Belvoir Priory, and an alabaster effigy was erected in St Mary the Virgin's Church, Bottesford,[131] on the right side of the altar. Seven years later, after his death at Baugé, an effigy of his son John was placed on the left.[132] De Ros left £400 to pay ten chaplains for eight years to educate his sons.[133]""",
    ]


@pytest.fixture
def sample_csv():
    return """category,subcategory,task
File System,File,Create a new File
File System,File,Edit the contents of a File
File System,File,Read the contents of a File"""


@pytest.mark.asyncio
async def test_simple_workflow(dria_client):
    simple = Simple()
    res = await dria_client.execute(
        Task(
            workflow=simple.workflow(prompt="Hey there!"),
            models=[Model.LLAMA3_1_8B_FP16],
        ),
        timeout=45,
    )
    result = simple.parse_result(res)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_code_workflow(dria_client):
    generate_code = GenerateCode()
    res = await dria_client.execute(
        Task(
            workflow=generate_code.workflow(
                instruction="Write a function to calculate the factorial of a number",
                language="python",
            ),
            models=[Model.QWEN2_5_CODER_7B_FP16],
        ),
        timeout=45,
    )
    result = generate_code.parse_result(res)
    assert isinstance(result, str)
    assert "def" in result  # Basic check that we got a function definition


@pytest.mark.asyncio
async def test_multihop_question_workflow(dria_client, text_chunks):
    mhop = MultiHopQuestion()
    res = await dria_client.execute(
        Task(
            workflow=mhop.workflow(chunks=text_chunks),
            models=[Model.GPT4O_MINI],
        ),
        timeout=45,
    )
    result = mhop.parse_result(res)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_csv_extender_pipeline(dria_client, sample_csv):
    await dria_client.initialize()
    pipeline = CSVExtenderPipeline(dria_client, PipelineConfig()).build(csv=sample_csv)
    result = await pipeline.execute(return_output=True)

    assert isinstance(result, dict)
    assert "rows" in result or "data" in result
