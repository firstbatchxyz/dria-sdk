from importlib.metadata import version, PackageNotFoundError

CORE_EXPORTS = [
    "recover_public_key",
    "uncompressed_public_key",
    "base64_to_json",
    "str_to_base64",
    "generate_task_keys",
    "logger",
    "FieldMapping",
    "FormatType",
    "DataFormatter",
    "ConversationMapping",
    "Helper",
    "SchemaParser",
    "select_nodes",
    "evaluate_nodes",
]

OPTIONAL_EXPORTS = [
    "NGramBasedDiversity",
    "VendiScore",
]

__all__ = CORE_EXPORTS.copy()

# Import crypto utilities
from .crypto import (
    recover_public_key,
    uncompressed_public_key,
    base64_to_json,
    str_to_base64,
    generate_task_keys,
)

# Import formatter utilities
from .formatter import FieldMapping, FormatType, DataFormatter, ConversationMapping

# Import logging utilities
from .logging.logging import logger

# Import helper
from .helper import Helper

# Import parsers
from .parsers.schema_parser import SchemaParser

# Import node selection utilities
from .node_selection import select_nodes, evaluate_nodes

try:
    from .metrics import NGramBasedDiversity, VendiScore

    version("dria[diversity]")
    __all__.extend(OPTIONAL_EXPORTS)
except (ImportError, PackageNotFoundError):
    pass
