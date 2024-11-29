import json
import re
from dria.models import TaskInput
from dria.factory.utilities import get_abs_path
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    GetAll,
    Workflow,
)
import logging
from typing import List
from dria.pipelines import Step, StepTemplate

try:
    import rank_bm25
    from nltk import tokenize
    import nltk
    import numpy as np
except ImportError as exc:
    raise ImportError(
        "SAFE requires additional dependencies. "
        "Please install them with: pip install dria[safe]"
    ) from exc

logger = logging.getLogger(__name__)

nltk.download("punkt_tab")
nltk.download("punkt", quiet=True)


def detect_initials(text):
    pattern = r"[A-Z]\. ?[A-Z]\."
    match = re.findall(pattern, text)
    return [m for m in match]


def fix_sentence_splitter(curr_sentences, initials):
    """Fix sentence splitter issues."""
    for initial in initials:
        if not np.any([initial in sent for sent in curr_sentences]):
            alpha1, alpha2 = [t.strip() for t in initial.split(".") if t.strip()]

            for i, (sent1, sent2) in enumerate(zip(curr_sentences, curr_sentences[1:])):
                if sent1.endswith(alpha1 + ".") and sent2.startswith(alpha2 + "."):
                    # merge sentence i and i+1
                    curr_sentences = (
                            curr_sentences[:i]
                            + [curr_sentences[i] + " " + curr_sentences[i + 1]]
                            + curr_sentences[i + 2 :]
                    )
                    break

    sentences, combine_with_previous = [], None

    for sent_idx, sent in enumerate(curr_sentences):
        if len(sent.split()) <= 1 and sent_idx == 0:
            assert not combine_with_previous
            combine_with_previous = True
            sentences.append(sent)
        elif len(sent.split()) <= 1:
            assert sent_idx > 0
            sentences[-1] += " " + sent
        elif sent[0].isalpha() and not sent[0].isupper() and sent_idx > 0:
            assert sent_idx > 0, curr_sentences
            sentences[-1] += " " + sent
            combine_with_previous = False
        elif combine_with_previous:
            assert sent_idx > 0
            sentences[-1] += " " + sent
            combine_with_previous = False
        else:
            assert not combine_with_previous
            sentences.append(sent)

    return sentences


def best_demos(sentence, few_shot_sentences, bm25, k=1):
    tokenized_query = sentence.split(" ")
    top_machings = bm25.get_top_n(tokenized_query, few_shot_sentences, k)
    return top_machings


def prepare_prompt(sentence: str) -> str:

    with open(get_abs_path("few_shots.json"), "r") as f:
        few_shots = json.load(f)

    with open(get_abs_path("prompt.md"), "r") as f:
        prompt = f.read()

    prompt += "\n"

    tokenized_corpus = [doc.split(" ") for doc in few_shots.keys()]
    bm25 = rank_bm25.BM25Okapi(tokenized_corpus)

    selected_few_shots = best_demos(sentence, list(few_shots.keys()), bm25, k=3)
    for few_shot in selected_few_shots:
        prompt += (
            "\nPlease breakdown the following sentence into independent facts:"
            " {}\n\n".format(few_shot)
        )
        for fact in few_shots[few_shot]:
            prompt += "- {}\n".format(fact)

    prompt += (
        "\nPlease breakdown the following sentence into independent facts:"
        " {}\n\n".format(sentence)
    )

    return prompt


class SplitAtomicFacts(StepTemplate):
    def create_workflow(
            self, instruction: str, question: str, response: str, **kwargs
    ) -> Workflow:
        """Split sentence to atomic facts.

        Args:
            :param instruction: Prompt for splitting atomic facts from response.
            :param response: Response to the question.
            :param question: The question.

        Returns:
            dict: The output data from the workflow.
        """
        builder = WorkflowBuilder(instruction=instruction)
        builder.set_max_time(self.config.max_time)
        builder.set_max_tokens(self.config.max_tokens)
        builder.set_max_steps(self.config.max_steps)

        # Step A: GenerateBackstory
        builder.generative_step(
            id="split_facts",
            prompt="{{instruction}}",
            operator=Operator.GENERATION,
            outputs=[Write.new("atomic_facts")],
        )

        flow = [Edge(source="split_facts", target="_end")]
        builder.flow(flow)
        builder.set_return_value("atomic_facts")
        return builder.build()

    def callback(self, step: Step) -> List[TaskInput]:
        """
        Process the output of the atomic facts

        Args:
            step (Step): The Step object containing input and output data.

        Returns:
            List[TaskInput]: A list of TaskInput objects for the next step.

        Raises:
            Exception: If there's an error processing the step output.
        """
        tasks = []
        for i, s in enumerate(step.output):
            try:
                input_params = step.input_params[s.id]
                for fact in self.parse(s.result):
                    tasks.append(
                        TaskInput(
                            atomic_fact=fact,
                            response=input_params.response,
                            question=input_params.question,
                        )
                    )
            except Exception as e:
                logger.error(f"Error in atomic fact split: {str(e)}")
        return tasks

    @staticmethod
    def parse(result: str) -> List[str]:
        """Parse the backstory JSON.

        Args:
            result (str): The JSON string containing the backstory.

        Returns:
            List[str]: The parsed backstory as a list of strings.
        """
        return [v.replace("\n", "").strip() for v in result.split("-") if v]
