Instruction:

Write three versions of a question (1-hop, 2-hop, and 3-hop) that all arrive at the same answer, using the following three documents as source material. 
Each version should require a different number of logical steps (hops) to reach the answer. 
Include the correct answer at the beginning.

Documents:

Document 1: {{document_1}}

Document 2: {{document_2}}

Document 3: {{document_3}}

## Guidelines:

Use information from each document to craft the question.
ensure the question logically connects details from all documents.
The question should be complex and require multi-step reasoning to answer.
The question must correspond accurately to the provided answer.

Start by generating question starting form 1-hop

1-hop question:
- Use information from single document to create a simple question leading to the answer.

2-hop question:
- Use information from 2 documents to create a question that requires two logical steps to answer.

3-hop question:
- Use information from all 3 documents to create a question that requires three logical steps to answer.


#### Example:

Document 1:
"Dunkirk is a 2017 historical war thriller film written, directed, and produced by Christopher Nolan that depicts the Dunkirk evacuation of World War II from the perspectives of the land, sea, and air."

Document 2:
"Interstellar is a 2014 epic science fiction film co-written, directed, and produced by Christopher Nolan."

Document C:
"Kip Thorne is an American theoretical physicist known for his contributions in gravitational physics and astrophysics. He consulted on the science fiction film ‘Interstellar’."

Answer: <answer>Dunkirk</answer>

1-hop question:
<1hop>What is the title of the war film directed by Christopher Nolan?</1hop>

2-hop question:
<2hop>What is the title of the war film directed by the director of Interstellar</2hop>

3-hop question:
<3hop>What is the title of the war film directed by the director who received advice from Kip Thorne in making a science fiction movie?<3hop>

---end of example---

Now generate the questions based on the provided documents. Use tags described in example to ouput 1,2,3 hop questions and the answer.
Output:

