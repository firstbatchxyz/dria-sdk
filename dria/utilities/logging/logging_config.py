import logging
from .rich_logging import configure_rich_logging


def configure_logging(log_level=logging.INFO):
    """
    Configure the logging system.
    This is a wrapper around configure_rich_logging to maintain backward compatibility.

    Args:
        log_level: The logging level to use. Defaults to INFO.
    """
    configure_rich_logging(log_level)


__all__ = ["configure_logging"]
