You will be given a predicted answer and a correct answer to a question. Your task is to classify the predicted answer based on how faithful and correct it is based on given question and context.

Here is the question:
<question>
{{question}}
</question>

Here is the context obtained with search related to the question.
<context>
{{context}}
</context>

Here is the predicted answer:
<prediction>
{{prediction}}
</prediction>

To complete this task:
1. Carefully read the question, context and the prediction.
2. Don't use your own knowledge to assess the prediction. Use only the provided context.
3. Determine if the predicted answer is truthful to given context and doesn't contradict it.
4. Make sure prediction doesn't contain information outside the scope of the context.

Use guidelines above to classify the prediction as:
- If the predicted answer is contextually and semantically correct, output only the label "[correct]" (without quotes).
- If the predicted answer is irrelevant, or ouf of scope ouput only the label "[irrelevant]" (without quotes).
- If the predicted answer is factually incorrect, output only the label "[incorrect]" (without quotes).
- If the predicted answer is partially correct, output only the label "[partially_correct]" (without quotes).

Do not provide any explanation or justification for your decision. Your entire response should consist of one of the labels:
- [correct]
- [irrelevant]
- [incorrect]
- [partially_correct]

Classification: