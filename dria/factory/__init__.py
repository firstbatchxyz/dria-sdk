from importlib.metadata import version, PackageNotFoundError

from .workflows import *
from .persona import *
from .subtopic import *
from .search import *
from .csv_extender import *
from .list_extender import *
from .qa_pipeline import *
from .nemotron_qa import *

__core_exports = [
    "Clair",
    "GenerateCode", 
    "IterateCode",
    "EvolveComplexity",
    "ScoreComplexity", 
    "EvolveInstruct",
    "EvolveQuality",
    "GenerateGraph",
    "TextRetrieval",
    "TextMatching",
    "TextClassification",
    "SemanticTriplet",
    "MagPie",
    "Simple",
    "EvaluatePrediction",
    "ValidatePrediction", 
    "SelfInstruct",
    "PersonaPipeline",
    "SubTopicPipeline",
    "WebMultiChoice",
    "SearchPipeline",
    "CSVExtenderPipeline",
    "ListExtenderPipeline",
    "QAPipeline",
    "MultiHopQuestion",
    "InstructionBacktranslation",
    "NemotronQA"
]

try:
    from .safe import *
    version("dria[safe]")
    __all__ = [*__core_exports, "SearchAugmentedFactualityEvaluator"]
except (ImportError, PackageNotFoundError):
    __all__ = __core_exports
