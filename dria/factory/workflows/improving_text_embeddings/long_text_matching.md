You have been assigned a text matching task: {{task}}

Your mission is to write one example for this task in JSON format. The JSON object must contain the following keys:
 - "input": a string, a random input specified by the task.
 - "positive_document": a string, a relevant document for the "input" according to the task.

Please adhere to the following guidelines:
 - The values of all fields should be in {{language}}.
 - Both the "input" and "positive_document" should be long documents (at least 300 words), avoid substantial word overlaps, otherwise the task would be too easy.
 - The "input" and "positive_document" should be independent of each other.

Your output must always be a JSON object only, do not explain yourself or output anything else. Be creative!
