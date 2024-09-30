import logging
import sys

from dria import constants


def configure_logging(level=constants.LOG_LEVEL):
    root_logger = logging.getLogger("dria")
    root_logger.setLevel(level or "INFO")

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress logs from specific libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False

    # Remove any existing handlers to prevent double logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)
