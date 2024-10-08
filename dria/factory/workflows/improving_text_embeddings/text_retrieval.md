You have been assigned a retrieval task: {{task}}

Your mission is to write one text retrieval example for this task in JSON format. The JSON object must contain the following keys:
 - "user_query": a string, a random user search query specified by the retrieval task.
 - "positive_document": a string, a relevant document for the user query.
 - "hard_negative_document": a string, a hard negative document that only appears relevant to the query.

Please adhere to the following guidelines:
 - The "user_query" should be {{query_type}}, {{query_length}}, {{clarity}}, and diverse in topic.
 - All documents must be created independent of the query. Avoid copying the query verbatim. It's acceptable if some parts of the "positive_document" are not topically related to the query.
 - All documents should be at least {{num_words}} words long.
 - The "hard_negative_document" contains some useful information, but it should be less useful or comprehensive compared to the "positive_document".
 - Both the query and documents should be in {{language}}.
 - Do not provide any explanation in any document on why it is relevant or not relevant to the query.
 - Both the query and documents require {{difficulty}} level education to understand.

Your output must always be a JSON object only, do not explain yourself or output anything else. Be creative!