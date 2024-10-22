Instruction:
In document question-answering tasks, there is a category of questions known as single-hop questions. The optimal strategy for solving this type of question is to split the document into multiple independent
chunks and then select the most suitable chunk based on the query; for chain reasoning questions, such as finding citation and reference relationships among multiple given papers, the optimal strategy is to present
the information in the document in the form of a graph; for statistical questions, such as analyzing and comparing financial data of multiple companies, the optimal strategy is to present the information in the
document in the form of a table; for configuration questions, such as needing to assemble a computer from a large batch of different models and components based on specific user needs, the optimal strategy is to
present the information in the document in the form of an algorithm; for summary questions, such as summarizing a large-scale meeting record into a meeting summary, the optimal strategy is to organize the
meeting records into a catalogue format.
Requirements:
A diversity of content needs to be generated, covering various fields and scenarios.
1.Adhere to the approach indicated in the Examples, that is, when performing question-answering tasks on such document collections, the optimal strategy is to split the documents into multiple independent chunks.
2.Use DOCUMENTS_INFO and QUERY as markers, with ## as a separator between each output.
Examples:
########
DOCUMENTS_INFO:
"Beethoven's Life", "Einstein's Life", "Newton's Life", "Da Vinci's Life", "Galileo's Life", "Voltaire's Life"
QUERY:
In which year was Newton born according to the given document collection?
##
DOCUMENTS_INFO:
2020 Financial Report of Netflix 2020 Financial Report of Alibaba 2020 Financial Report of Tencent
QUERY:
classify the companies in the above documents according to revenue, with more than 100 billion as high-income companies and less than 100 billion as low-income companies.
##
DOCUMENTS_INFO:
RAG: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks DPR: Dense Passage Retrieval for Open-Domain Question Answering BERT: Pre-training of Deep Bidirectional Transformers for
Language Understanding T5: Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer RoBERTa: A Robustly Optimized BERT Pretraining Approach ALBERT: A Lite BERT for Selfsupervised Learning of Language Representations
QUERY:
decide the reference and citation relationship among the given documents
########
Use the following topic to guide generation
{{topic}}
Output: