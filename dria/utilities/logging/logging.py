from .logging_config import configure_logging
from .rich_logging import logger, console

# Configure the logging
configure_logging()

__all__ = ["logger", "console"]
