Instruction:
To solve the complex document problem, you need to break down the given query into multiple relatively simple, independent sub-questions.
Requirements:
1.Knowledge Info is a description of the structured knowledge information, which you can refer to for the breakdown.
2.If the given question is already simple enough or cannot be broken down at all, then no breakdown is necessary.
Examples:
########
Knowledge Info:
We have chunks of "Judgment Document 7" \n "Judgment Document 3" \n "Judgment Document 2" \n "Judgment Document 4" \n "Judgment Document 6" \n "Judgment Document 8" \n "Judgment……
Query:
Please classify the above judgment documents according to the six categories: 'Ownership Dispute', 'Administrative Body - Labor and Social Security Administration (Labor, Social Security)', 'Execution Cause -
Non-litigation Administrative Execution', 'Embezzlement and Bribery', 'Execution Cause - Other Causes', and 'Administrative Action - Administrative Payment'. Just output the title of each judgment document.
Please respond in the format provided, and titles should correspond to the actual judgment documents: \n{{'Ownership Dispute': ['"Judgment Document a"', '"Judgment Document b"'], 'Administrative Body - Labor
and Social Security Administration (Labor, Social Security)': ['"Judgment Document a"', '"Judgment Document b”’], …….
Output:
Determine whether the given judgment document's cause is 'Ownership Dispute', determine whether the given judgment document's cause is 'Administrative Body - Labor and Social Security Administration (Labo
r, Social Security)', determine whether the given judgment document's cause is 'Execution Cause - Non-litigation Administrative Execution', determine whether the given judgment document's cause is 'Embezzlem
ent and Bribery', determine whether the given judgment document's cause is 'Execution Cause - Other Causes', determine whether the given judgment document's cause is 'Administrative Action - Administrative P
ayment'.
########
Knowledge Info: {{knowledge_info}}
Query: {{query}}
Output: