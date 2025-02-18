import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich import traceback

# Install rich traceback handler
traceback.install()

# Create custom theme for different log levels
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "debug": "green",
})

# Create console with custom theme
console = Console(theme=custom_theme)

def configure_rich_logging(log_level=logging.INFO):
    """
    Configure logging with Rich formatting for beautiful terminal output.
    
    Args:
        log_level: The logging level to use. Defaults to INFO.
    """
    # Create rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )

    # Configure root logger
    root_logger = logging.getLogger("dria")
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add rich handler
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(rich_handler)

    # Suppress logs from specific libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False

# Create a logger instance
logger = logging.getLogger("dria")

__all__ = ["logger", "configure_rich_logging", "console"] 