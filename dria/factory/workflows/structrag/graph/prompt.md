Instruction:
According to the requirements described in the Requirement section, extract the necessary triples from the Raw Content.
The triples should be output on one line in the format: {{'head': '...', 'relation': '...', 'tail': ['...', '...']}}.
Note: Instead of extracting all triples from the text, analyze the relationships and entities mentioned in the Requirement and only extract the relevant triples.
Additionally, ensure that the 'head' and 'tail' in your output are as complete as possible. They can consist of more than just a single word or phrase—they may also be sentences or paragraphs of text. Aim to keep th
em consistent with the original text without any abbreviations.
Examples:
########
{{"head": "LLM4Vuln: A Unified Evaluation Framework for Decoupling and Enhancing LLMs\' Vulnerability Reasoning", "relation": "reference", "tail": ["Why Can GPT Learn In-Context? Language Models
Implicitly Perform Gradient Descent as Meta-Optimizers.", "Can Large Language Models Be an Alternative to Human Evaluations?"]}}
########
Raw Documents:
{{documents}}
Query:
{{query}}
Output: