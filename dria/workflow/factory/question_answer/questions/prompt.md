You will be provided with a detailed backstory, a context and a history of previously asked questions. \\nYour task is
to generate a single, specific question about the given context based on the backstory of persona, who wants to learn
more about the topic. You'll do this by first generating rationales based on your backstory, and then the question based
on rationales directed to provided context.\\n\\nYour backstory:\\n<backstory>\\n{{persona}}\\n</backstory>\\n\\nHere
is the context:\\n<context>\\n{{context}}\\n</context>\\n\\nGuidelines for generating the question:\\n1. The question
should be directly related to a specific part of the context.\\n2. Frame the rationale from a user's backstory, as if
they are seeking to learn more about the provided context to maximize their gains.\\n3. Do not reveal ANY information
about the backstory in your question.\\n4. Ensure the question is clear, concise, and can be answered using information
from the context.\\n5. The question should be designed to aid in information retrieval and intelligence building.\\n6.
Avoid generating a question that is the same as or very similar to any of the questions in the question history.\\n7.
Avoid asking multiple questions in one.\\n\\nHere is the history of previously asked questions:\\n<question_history>
\\n{{history}}\\n</question_history>\\n\\nImportant: Avoid generating a question that is the same as or very similar to
any of the questions in the question history.\\n\\nPlease generate a single question based on the context and following
the guidelines above. Provide your generated question within <generated_question> tags. Generate rationales
within <rationale> tags