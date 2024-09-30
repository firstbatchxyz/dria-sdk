import logging
from dria.utils.logging_config import configure_logging

# Configure the logging
configure_logging()

# Create a logger instance
logger = logging.getLogger(__name__)

# Export the logger
__all__ = ['logger']