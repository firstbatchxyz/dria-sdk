class RPCClientError(Exception):
    """Base class for RPC client exceptions."""


class RPCContentTopicError(RPCClientError):
    """Raised when there is an error fetching or pushing content to a topic."""

    def __init__(self, msg: str, topic: str):
        """
        Initialize the RPCContentTopicError.

        Args:
            msg (str): The exception message.
            topic (str): The content topic where the error occurred.
        """
        super().__init__(f"{msg} (Topic: {topic})")
        self.topic = topic


class RPCConnectionError(RPCClientError):
    """Raised when there is a connection error with the RPC server."""

    def __init__(self, msg: str):
        """
        Initialize the RPCConnectionError.

        Args:
            msg (str): The exception message.
        """
        super().__init__(f"Connection error: {msg}")


class RPCAuthenticationError(RPCClientError):
    """Raised when there is an authentication error with the RPC server."""

    def __init__(self):
        """Initialize the RPCAuthenticationError."""
        super().__init__("Authentication failed. Please check your auth token.")


class TaskPublishError(Exception):
    """Raised when there is an error publishing a task."""

    def __init__(self, msg: str):
        """
        Initialize the TaskPublishError.

        Args:
            msg (str): The exception message.
        """
        super().__init__(f"Task publish error: {msg}")


class TaskFilterError(Exception):
    """Raised when there is an error filtering a task."""

    def __init__(self, msg: str):
        """
        Initialize the TaskFilterError.
        """
        super().__init__(f"Failed to create filter: {msg}")