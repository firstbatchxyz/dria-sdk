# Overview

Dria factory provides a set of built-in tasks and pipelines for generating synthetic data, code, and other artifacts. 
These tasks are designed to be used in conjunction with the Dria client to create complex workflows for generating synthetic data.


#### CLAIR
[`Clair`](factory/clair.md) is a task that takes a student solution and reasoning, and corrects the student solution.

#### GenerateCode
[`GenerateCode`](factory/code_generation.md) is a task that generates code based on an instruction and specified programming language.

#### ScoreComplexity

[`ScoreComplexity`](factory/complexity_scorer.md) is a task that ranks a list of instructions based on their complexity.

#### EvaluatePrediction

[`EvaluatePrediction`](factory/evaluate.md) is a task that evaluates if a predicted answer is contextually and semantically correct compared to the correct answer.

#### EvolveComplexity

[`EvolveComplexity`](factory/evolve_complexity.md) is a task that increases the complexity of a given instruction.

#### GenerateGraph

[`GenerateGraph`](factory/graph_builder.md) is a task that generates a graph of concepts and their relationships from a given context.

#### EvolveInstruct

[`EvolveInstruct`](factory/instruction_evolution.md) is a task that mutates a given prompt based on a specified mutation type.

#### IterateCode

[`IterateCode`](factory/iterate_code.md) is a task that iterates and improves existing code based on given instructions.

#### MagPie

[`MagPie`](factory/magpie.md) is a task that generates a dialogue between two personas.

#### PersonaPipeline

[`PersonaPipeline`](factory/persona.md) is a class that creates a pipeline for generating personas based on a simulation description.

#### EvolveQuality

[`EvolveQuality`](factory/quality_evolution.md) is a task that evolves the quality of a response to a prompt through rewriting based on a specified method.

#### SearchPipeline

[`SearchPipeline`](factory/search.md) is a class that creates a pipeline for searching and retrieving data from the web based on a given topic.

#### SelfInstruct

[`SelfInstruct`](factory/self_instruct.md) is a task that generates user queries for a given AI application and context.


#### SemanticTriplet

[`SemanticTriplet`](factory/semantic_triplet.md) is a task that generates a JSON object containing three textual units with specified semantic similarity scores.

#### Simple

[`Simple`](factory/simple.md) is a task that generates text based on instruction.

#### SubTopicPipeline

[`SubTopicPipeline`](factory/subtopic.md) is a class that creates a pipeline for generating subtopics based on a given topic. The pipeline recursively generates subtopics with increasing depth.

#### TextClassification

[`TextClassification`](factory/text_classification.md) is a task that generates a JSON object containing an example for a text classification task.

#### TextMatching

[`TextMatching`](factory/text_matching.md) is a task that generates a JSON object with 'input' and 'positive_document' for a specified text matching task.

#### TextRetrieval

[`TextRetrieval`](factory/text_retrieval.md) is a task that generates a JSON object containing a user query, a positive document, and a hard negative document for a specified text retrieval task.

#### ValidatePrediction

[`ValidatePrediction`](factory/validate.md) is a task that determines if a predicted answer is contextually and semantically correct compared to a given correct answer.

#### WebMultiChoice

[`WebMultiChoice`](factory/web_multi_choice.md) is a task that answers multiple-choice questions using web search and evaluation.
