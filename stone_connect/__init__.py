"""Stone Connect Heater Python Library.

Async Python library for controlling Stone Connect WiFi electric heaters.
"""

from stone_connect.client import StoneConnectHeater
from stone_connect.exceptions import (
    StoneConnectAPIError,
    StoneConnectAuthenticationError,
    StoneConnectConnectionError,
    StoneConnectError,
    StoneConnectValidationError,
)
from stone_connect.models import (
    Info,
    OperationMode,
    Schedule,
    ScheduleDay,
    ScheduleSlot,
    Status,
    UseMode,
    parse_timestamp,
)

__version__ = "0.1.1"
__all__ = [
    "StoneConnectHeater",
    "Info",
    "Status",
    "Schedule",
    "OperationMode",
    "ScheduleDay",
    "ScheduleSlot",
    "UseMode",
    "parse_timestamp",
    "StoneConnectError",
    "StoneConnectConnectionError",
    "StoneConnectAuthenticationError",
    "StoneConnectAPIError",
    "StoneConnectValidationError",
]
