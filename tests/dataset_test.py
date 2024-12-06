from dria import DriaDataset, DatasetGenerator, Model
from dria.factory import MagPie
import asyncio
from dria.utils import ConversationMapping, FieldMapping, FormatType


instructions = [
    {
        "instructor_persona": "A math student",
        "responding_persona": "An AI teaching assistant.",
        "num_turns": 3,
    },
    {
        "instructor_persona": "A chemistry student",
        "responding_persona": "An AI teaching assistant.",
        "num_turns": 3,
    },
    {
        "instructor_persona": "A physics student",
        "responding_persona": "An AI teaching assistant.",
        "num_turns": 3,
    },
    {
        "instructor_persona": "A music student",
        "responding_persona": "An AI teaching assistant.",
        "num_turns": 5,
    },
    {
        "instructor_persona": "A visual arts student",
        "responding_persona": "An AI teaching assistant.",
        "num_turns": 2,
    },
]

my_dataset = DriaDataset("magpie_test", "a test dataset", MagPie.OutputSchema)
generator = DatasetGenerator(dataset=my_dataset)


asyncio.run(
    generator.generate(
        instructions,
        MagPie,
        [
            Model.ANTHROPIC_HAIKU_3_5_OR,
            Model.QWEN2_5_72B_OR,
            Model.LLAMA_3_1_8B_OR,
            Model.LLAMA3_1_8B_FP16,
        ],
    )
)

cmap = ConversationMapping(
    conversation=FieldMapping(user_message="instructor", assistant_message="responder"),
    field="dialogue",
)
my_dataset.format_for_training(
    FormatType.CONVERSATIONAL_PROMPT_COMPLETION, cmap, output_format="jsonl"
)
