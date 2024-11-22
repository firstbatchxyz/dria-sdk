import string
from abc import abstractmethod
from collections import Counter, defaultdict

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim
    from tqdm import tqdm
    from vendi_score import vendi
except ImportError as exc:
    raise ImportError(
        "Diversity metrics require additional dependencies. "
        "Please install them with: pip install dria[diversity]"
    ) from exc


DEFAULT_EMBEDDING_MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"


class EmbeddingModel:
    def __init__(self, model_path_or_name=DEFAULT_EMBEDDING_MODEL_NAME):
        self.model_path_or_name = model_path_or_name
        self.model = SentenceTransformer(model_path_or_name, truncate_dim=512)

    def embed(self, docs, batch_size=100):
        n_batches = int(np.ceil(len(docs) / batch_size))
        all_embeddings = []
        for i in tqdm(range(n_batches), total=n_batches):
            embeddings = self.model.encode(docs[i * batch_size : (i + 1) * batch_size])
            all_embeddings.append(embeddings)
        return np.concatenate(all_embeddings, axis=0)


class DiversityMetric:
    @abstractmethod
    def calculate(self, data_points, data_labels=None, **kwargs):
        pass


class VendiScore(DiversityMetric):
    """
    Implementation based on https://arxiv.org/pdf/2210.02410
    """

    def __init__(self, embedder=None, similarity_function=None):
        super().__init__()
        if embedder is None:
            embedder = EmbeddingModel()
        if similarity_function is None:
            similarity_function = cos_sim
        self.embedder = embedder
        self.similarity_function = similarity_function

    def calculate(self, data_points, data_labels=None, **kwargs):
        if type(data_points) is not np.ndarray:
            data_points = self.embedder.embed(data_points)
        return vendi.score(data_points, self.similarity_function)


class NGramBasedDiversity(DiversityMetric):
    def __init__(self, max_n_gram_size=3):
        super().__init__()
        self.max_n_gram_size = max_n_gram_size

    @staticmethod
    def normalise_string(doc):
        return doc.lower().translate(str.maketrans("", "", string.punctuation))

    @staticmethod
    def find_ngrams(doc, n_gram_size, only_unique=True):
        doc = NGramBasedDiversity.normalise_string(doc)
        word_list = doc.strip().split()
        if len(word_list) < n_gram_size:
            return []
        n_grams = []
        for i in range(n_gram_size, len(word_list) + 1):
            n_grams.append(" ".join(word_list[i - n_gram_size : i]))
        if only_unique:
            n_grams = list(set(n_grams))
        return n_grams

    def calculate(self, docs, data_labels=None, **kwargs):
        return_n_gram_distribution = kwargs.get("return_n_gram_distribution", False)
        assert len(docs) > 0, "there is no datapoints"
        counters = defaultdict(Counter)
        report = defaultdict(dict)
        for n_gram_size in range(1, self.max_n_gram_size + 1):
            for doc in docs:
                n_grams = self.find_ngrams(doc, n_gram_size)
                counters[n_gram_size].update(n_grams)
            n_gram_count = len(counters[n_gram_size])
            ngram_probs = (
                np.array(list(counters[n_gram_size].values()))
                / counters[n_gram_size].total()
            )
            entropy = (-ngram_probs * np.log(ngram_probs)).sum()
            max_entropy = np.log(n_gram_count)
            report[n_gram_size] = {
                "n_gram_count": n_gram_count,
                "entropy": entropy,
                "normalised_entropy": entropy / max_entropy,
            }
            if return_n_gram_distribution:
                report[n_gram_size]["n_gram_distribution"] = dict(counters[n_gram_size])
        return dict(report)
