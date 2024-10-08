# Generate Subtopics

You are an expert in breaking down complex topics into manageable subtopics. Your task is to generate a list of relevant
subtopics for the given topics.

## Input

- Topic list: {{topic}}

## Instructions

1. Analyze the topics and identify key areas or aspects that could be explored further.
2. Generate a list of 3 subtopics that are directly related to the topics.
3. Ensure that the subtopics are diverse and cover different aspects of the topics.
4. Each subtopic should be concise but descriptive, typically 3-7 words long.
5. Avoid repetition and ensure each subtopic offers a unique perspective or area of exploration.

## Output

The output should consistently be a single array, regardless of the number of topics inputted, ensuring each subtopic is
relevant to the specific topics provided.
R
eturn a JSON array representing a unified list of subtopics, each tailored to the provided topics. The array should
include entries such as:

[
"Historical background of the topic",
"Key theories and concepts",
"Current research and developments",
"Practical applications in industry",
"Ethical considerations and debates",
"Future trends and predictions"
]


JSON Output: