"""Stone Connect Heater exceptions."""


class StoneConnectError(Exception):
    """Base exception for Stone Connect Heater errors."""


class StoneConnectConnectionError(StoneConnectError):
    """Connection-related errors."""


class StoneConnectAuthenticationError(StoneConnectError):
    """Authentication-related errors."""


class StoneConnectAPIError(StoneConnectError):
    """API-related errors."""


class StoneConnectValidationError(StoneConnectError):
    """Validation-related errors."""
