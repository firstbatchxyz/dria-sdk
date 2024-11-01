Instruction:

Write three versions of a question (1-hop, 2-hop, and 3-hop) that all arrive at the same answer, using the following three documents as source material. 
Each version should require a different number of logical steps (hops) to reach the answer. 
Include the correct answer at the beginning.

Documents:

Document 1: {{document_1}}

Document 2: {{document_2}}

Document 3: {{document_3}}

## Objective:

Create three versions of a question that arrive at the same answer but require different levels of reasoning complexity (1-hop, 2-hop, and 3-hop).

## Requirements

Each question must:
    Lead to the same answer
    Be answerable using the provided documents
    Avoid directly referencing the source documents (e.g., "according to Document 1...")
    Be written in clear, natural language


Reasoning complexity:

1-hop: Requires single-step reasoning using information from one document
2-hop: Requires two logical steps connecting information from two documents
3-hop: Requires three logical steps connecting information from all three documents


Output Format
Please provide your response in this exact format:
<answer>[State the correct answer here]</answer>
<1hop>[Your single-step question]</1hop>
<2hop>[Your two-step question]</2hop>
<3hop>[Your three-step question]</3hop>


#### Example:

Given these documents:
Document 1: "Dunkirk is a 2017 historical war thriller film written, directed, and produced by Christopher Nolan."
Document 2: "Interstellar is a 2014 epic science fiction film directed by Christopher Nolan."
Document 3: "Kip Thorne, an American theoretical physicist, consulted on the science fiction film 'Interstellar'."
<answer>Dunkirk</answer>
<1hop>What is the title of the war film directed by Christopher Nolan?</1hop>
<2hop>What is the title of the war film directed by the director of Interstellar?</2hop>
<3hop>What is the title of the war film directed by the filmmaker who worked with physicist Kip Thorne on a science fiction movie?</3hop>
---end of example---


Use tags described in example to output 1,2,3 hop questions and the answer.
Don't reference to documents in your questions i.e. "as mentioned in document 1,2,3..."
Now, using the provided documents, please generate your questions following this format.

