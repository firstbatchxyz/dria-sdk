You have been assigned a text classification task: {{task}}

Your mission is to write one text classification example for this task in JSON format. The JSON object must contain the following keys:
 - "input_text": a string, the input text specified by the classification task.
 - "label": a string, the correct label of the input text.
 - "misleading_label": a string, an incorrect label that is related to the task.

Please adhere to the following guidelines:
 - The "input_text" should be diverse in expression.
 - The "misleading_label" must be a valid label for the given task, but not as appropriate as the "label" for the "input_text".
 - The values for all fields should be in {{language}}.
 - Avoid including the values of the "label" and "misleading_label" fields in the "input_text", that would make the task too easy.
 - The "input_text" is {{clarity}} and requires {{difficulty}} level education to comprehend.

Your output must always be a JSON object only, do not explain yourself or output anything else. Be creative!