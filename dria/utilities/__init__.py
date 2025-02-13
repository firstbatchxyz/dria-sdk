from importlib.metadata import version, PackageNotFoundError

from .crypto import (
    recover_public_key,
    uncompressed_public_key,
    generate_task_keys,
    base64_to_json,
    str_to_base64,
)
from logging.logging import logger
from .formatter import ConversationMapping, FieldMapping, DataFormatter, FormatType
from .helper import Helper
from .parsers.schema_parser import SchemaParser
from .node_selection import select_nodes, evaluate_nodes

__core_exports = [
    "recover_public_key",
    "uncompressed_public_key",
    "base64_to_json",
    "str_to_base64",
    "generate_task_keys",
    "logger",
    "FieldMapping",
    "FormatType",
    "DataFormatter",
]

try:
    from .metrics import NGramBasedDiversity, VendiScore

    version("dria[diversity]")
    __all__ = [*__core_exports, "NGramBasedDiversity", "VendiScore"]
except (ImportError, PackageNotFoundError):
    __all__ = __core_exports
