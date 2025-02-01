from importlib.metadata import version, PackageNotFoundError

from dria.utils.crypto import (
    recover_public_key,
    uncompressed_public_key,
    generate_task_keys,
    base64_to_json,
    str_to_base64,
)
from .logging import logger
from .formatter import ConversationMapping, FieldMapping, DataFormatter, FormatType

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
