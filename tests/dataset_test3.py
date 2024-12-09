# yalandan
import sys
import os

##
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from dria import DriaDataset, DatasetGenerator, Model
from dria.factory.subtopic import GenerateSubtopics
import asyncio
from dria.utils import ConversationMapping, FieldMapping, FormatType


my_dataset = DriaDataset(
    name="subtopics",
    description="A dataset for subtopics",
    schema=GenerateSubtopics.OutputSchema,
)
generator = DatasetGenerator(dataset=my_dataset)


instructions = [
    {"topic": "python language"},
    {"topic": "rust language"},
    {"topic": "slack api"},
]

# asyncio.run(
#     generator.generate(
#         instructions=instructions,
#         singletons=GenerateSubtopics,
#         models=[Model.ANTHROPIC_HAIKU_3_5_OR],
#     )
# )
entries = my_dataset.get_entries(True)
print(json.dumps(entries, indent=2, ensure_ascii=False))

""""
from dria import Prompt
from pydantic import BaseModel
class TranslatedTopic(BaseModel):
    subtopic: str
    turkish_subtopic: str


prompter = Prompt("write the given subtopic {{subtopic}} in turkish", schema=TranslatedTopic)
asyncio.run(generator.transform_and_update_dataset(prompter, models=Model.GPT4O))
"""

"""
my_dataset.format_for_training(
  FormatType.STANDARD_PROMPT_COMPLETION, FieldMapping(prompt="topic", completion="subtopic"), output_format="jsonl", output_path="subtopicsX"
)
"""
