Write a {{unit}} triple with varying semantic similarity scores in JSON format. The semantic similarity score ranges from 1 to 5, with 1 denotes least similar and 5 denotes most similar.

Please adhere to the following guidelines:
 - The keys in JSON are "S1", "S2", and "S3", the values are all strings in {{language}}, do not add any other keys.
 - There should be some word overlaps between all three {{unit}}s.
 - The similarity score between S1 and S2 should be {{high_score}}.
 - The similarity score between S1 and S3 should be {{low_score}}.
 - The {{unit}}s require {{difficulty}} level education to understand and should be diverse in terms of topic and length.

Your output must always be a JSON object only with three keys "S1", "S2" and "S3", do not explain yourself or output anything else. Be creative!