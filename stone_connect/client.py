"""Stone Connect Heater client."""

import base64
import json
import logging
from typing import Any, Dict, Optional, Tuple

import aiohttp

from stone_connect.exceptions import (
    StoneConnectAPIError,
    StoneConnectAuthenticationError,
    StoneConnectConnectionError,
    StoneConnectValidationError,
)
from stone_connect.models import (
    Info,
    OperationMode,
    Schedule,
    Status,
)

_LOGGER = logging.getLogger(__name__)


class StoneConnectHeater:
    """
    Async client for Stone Connect WiFi Electric Heater.

    This client provides methods to control and monitor Stone Connect heaters
    via their local HTTPS API.
    """

    # Default credentials found in the decompiled APK
    DEFAULT_USERNAME = "App_RadWiFi_v1"
    DEFAULT_PASSWORD = "e1qf45s4w8e7q5wda4s5d1as2"

    def __init__(
        self,
        host: str,
        port: int = 443,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
        timeout: int = 30,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Initialize the heater client.

        Args:
            host: IP address or hostname of the heater
            port: HTTPS port (default: 443)
            username: Authentication username (default: App_RadWiFi_v1)
            password: Authentication password (default: e1qf45s4w8e7q5wda4s5d1as2)
            timeout: Request timeout in seconds
            session: Optional existing aiohttp session to use
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session = session
        self._owned_session = session is None

        self.base_url = f"https://{host}:{port}/Domestic_Heating/Radiators/v1"

        # Create auth header
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"

    async def __aenter__(self) -> "StoneConnectHeater":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self._session = aiohttp.ClientSession(
                raise_for_status=True,
                connector=connector,
                timeout=timeout,
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                    "User-Agent": "StoneConnect-Python-Client/1.0",
                },
            )
        return self._session

    async def close(self) -> None:
        """Close the client session."""
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the heater API.

        Args:
            method: HTTP method (GET, PUT, POST, etc.)
            endpoint: API endpoint (without leading slash)
            data: Optional JSON data to send

        Returns:
            Parsed JSON response

        Raises:
            StoneConnectConnectionError: If the request fails
            StoneConnectAuthenticationError: If authentication fails
            StoneConnectAPIError: For other API errors
        """
        session = await self._ensure_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            _LOGGER.debug(f"Making {method} request to {url}")

            kwargs: Dict[str, Any] = {"method": method, "url": url}
            if data is not None:
                kwargs["json"] = data

            async with session.request(**kwargs) as response:
                response_text = await response.text()

                if response.status == 401:
                    raise StoneConnectAuthenticationError("Authentication failed")
                elif response.status == 404:
                    raise StoneConnectAPIError(f"Endpoint not found: {endpoint}")
                elif not response.ok:
                    raise StoneConnectAPIError(
                        f"API request failed: {response.status} - {response_text}"
                    )

                # Try to parse JSON response
                try:
                    return await response.json(content_type="text/json")
                except json.JSONDecodeError:
                    # Some endpoints might return plain text or empty responses
                    return {"response": response_text} if response_text else {}

        except aiohttp.ClientError as e:
            raise StoneConnectConnectionError(f"Connection failed: {e}")

    async def get_info(self) -> Info:
        """
        Get device information from /info endpoint.

        Returns:
            Info object with device details
        """
        try:
            data = await self._request("GET", "info")
            return Info.from_dict(data)
        except Exception as e:
            _LOGGER.error(f"Failed to get device info: {e}")
            raise

    async def get_status(self) -> Status:
        """
        Get current device status from /Status endpoint.

        Returns:
            Status object with current state
        """
        try:
            data = await self._request("GET", "status")
            return Status.from_dict(data)
        except Exception as e:
            _LOGGER.error("Failed to get device status: %s", e)
            raise

    async def get_schedule(self) -> Schedule:
        """
        Get weekly schedule from /Schedule endpoint.

        Returns:
            Schedule object with schedule data
        """
        try:
            data = await self._request("GET", "Schedule")
            return Schedule.from_dict(data)
        except Exception as e:
            _LOGGER.error("Failed to get schedule: %s", e)
            raise

    async def set_temperature_and_mode(
        self, temperature: float, mode: OperationMode
    ) -> None:
        """
        Set both temperature and operation mode in a single call.

        Args:
            temperature: Target temperature in Celsius (0-30°C, ignored for power modes)
            mode: Operation mode

        Raises:
            StoneConnectValidationError: If temperature is outside 0-30°C range
        """
        try:
            # Validate temperature range for modes that use temperature setpoints
            if not mode.is_power_mode():
                self._validate_temperature(temperature)

            # Get device info to obtain Client_ID
            device_info = await self.get_info()
            client_id = device_info.client_id

            # Build the request body
            body: Dict[str, Any] = {
                "Client_ID": client_id,
                "Operative_Mode": mode.value,
            }

            # Only include Set_Point for modes that use temperature setpoints
            if not mode.is_power_mode():
                body["Set_Point"] = temperature
                log_message = "Set temperature to %s°C and mode to %s"
                log_args: Tuple[Any, ...] = (temperature, mode.value)
            else:
                body["Set_Point"] = 0
                log_message = "Set mode to %s (power mode, no temperature)"
                log_args = (mode.value,)

            await self._request("PUT", "setpoint", body)
            _LOGGER.info(log_message, *log_args)
        except Exception as e:
            _LOGGER.error("Failed to set temperature and mode: %s", e)
            raise

    async def set_temperature(
        self, temperature: float, mode: Optional[OperationMode] = None
    ) -> None:
        """
        Set target temperature and optionally operation mode.

        Note: This method only works with modes that accept custom temperatures:
        - MANUAL: Manual temperature control
        - BOOST: Boost mode with custom temperature

        For preset modes (COMFORT, ECO, ANTIFREEZE), use set_operation_mode() instead.
        Power modes (HIGH, MEDIUM, LOW) don't use temperature setpoints.

        Args:
            temperature: Target temperature in Celsius (0-30°C)
            mode: Optional operation mode (if not provided, will get current mode from device)

        Raises:
            StoneConnectValidationError: If temperature is outside range or mode doesn't support custom temperatures
        """
        # Validate temperature range
        self._validate_temperature(temperature)

        if mode is None:
            # Get current mode from device
            status = await self.get_status()
            mode = status.operative_mode or OperationMode.MANUAL

        # Validate that the mode supports custom temperature setpoints
        if not mode.is_custom_mode():
            if mode.is_power_mode():
                raise StoneConnectValidationError(
                    f"Power mode {mode.value} doesn't use temperature setpoints. Use set_operation_mode() instead."
                )
            elif mode.is_preset_mode():
                raise StoneConnectValidationError(
                    f"Preset mode {mode.value} uses predefined temperature. Use set_operation_mode() instead."
                )
            else:
                raise StoneConnectValidationError(
                    f"Mode {mode.value} doesn't support custom temperature setpoints."
                )

        await self.set_temperature_and_mode(temperature, mode)

    async def set_operation_mode(self, mode: OperationMode) -> None:
        """
        Set operation mode. Automatically handles temperature setpoints based on mode type:

        - Power modes (HIGH, MEDIUM, LOW): Don't use temperature setpoints
        - Preset modes (COMFORT, ECO, ANTIFREEZE): Use predefined temperatures from device settings
        - Custom modes (MANUAL, BOOST): Keep current temperature or use default
        - Other modes (STANDBY, SCHEDULE, HOLIDAY): Keep current temperature

        Args:
            mode: Operation mode to set

        Returns:
            True if successful
        """
        # Get device info and current status
        device_info = await self.get_info()

        # Determine appropriate temperature setpoint based on mode
        if mode.is_power_mode():
            # Power modes don't use temperature setpoints - set to 0 or current
            temperature = 0.0  # Power modes typically don't need a temperature
        elif mode.is_preset_mode():
            # Use preset temperature from device settings
            preset_temp = mode.get_preset_setpoint(device_info)
            if preset_temp is None:
                raise StoneConnectValidationError(
                    f"No preset temperature found for mode {mode.value}"
                )
            temperature = preset_temp
        else:
            # For other modes, keep current temperature or use reasonable default
            status = await self.get_status()
            temperature = status.set_point or 20.0  # Default to 20°C if no current temp

        await self.set_temperature_and_mode(temperature, mode)

    async def is_online(self) -> bool:
        """
        Check if device is online and responding.

        Returns:
            True if device is online and responding
        """
        try:
            await self.get_status()
            return True
        except Exception:
            return False

    async def has_power_measurement_support(self) -> bool:
        """
        Determine if the device supports power measurement capability.

        This method asynchronously checks whether the connected device has power measurement
        functionality by examining the Load_Size_Watt field from the device information.
        """
        info = await self.get_info()
        return info.load_size_watt != 0

    # Convenience methods
    async def set_comfort_mode(self) -> None:
        """Set heater to comfort mode using the predefined comfort temperature."""
        await self.set_operation_mode(OperationMode.COMFORT)

    async def set_eco_mode(self) -> None:
        """Set heater to eco mode using the predefined eco temperature."""
        await self.set_operation_mode(OperationMode.ECO)

    async def set_antifreeze_mode(self) -> None:
        """Set heater to antifreeze mode using the predefined antifreeze temperature."""
        await self.set_operation_mode(OperationMode.ANTIFREEZE)

    async def set_manual_temperature(self, temperature: float) -> None:
        """Set heater to manual mode with a specific temperature."""
        await self.set_temperature(temperature, OperationMode.MANUAL)

    async def set_power_mode(self, power_level: OperationMode) -> None:
        """Set heater to a power-based mode (HIGH, MEDIUM, LOW)."""
        if not power_level.is_power_mode():
            raise StoneConnectValidationError(
                f"{power_level.value} is not a valid power mode. Use HIGH, MEDIUM, or LOW."
            )
        await self.set_operation_mode(power_level)

    async def set_standby(self) -> None:
        """Set heater to standby mode (essentially off but still connected)."""
        await self.set_operation_mode(OperationMode.STANDBY)

    # Property-like methods for convenience
    async def get_current_temperature(self) -> Optional[float]:
        """Get current temperature from device info (not available in status)."""
        info = await self.get_info()
        return info.set_point  # Current setpoint, no actual temperature sensor

    async def get_target_temperature(self) -> Optional[float]:
        """Get target temperature."""
        status = await self.get_status()
        return status.set_point

    async def is_heating(self) -> Optional[bool]:
        """Check if device is currently heating (any mode other than STANDBY)."""
        status = await self.get_status()
        if status.operative_mode is None:
            return None
        return status.operative_mode != OperationMode.STANDBY

    async def get_signal_strength(self) -> Optional[int]:
        """Get WiFi signal strength (RSSI)."""
        status = await self.get_status()
        return status.rssi

    async def is_locked(self) -> Optional[bool]:
        """Check if device is locked."""
        status = await self.get_status()
        return status.lock_status

    async def get_error_code(self) -> Optional[int]:
        """Get current error code (0 = no error)."""
        status = await self.get_status()
        return status.error_code

    async def get_daily_energy(self) -> Optional[int]:
        """Get daily energy consumption."""
        status = await self.get_status()
        return status.daily_energy

    async def get_power_consumption(self) -> Optional[int]:
        """Get current power consumption in watts."""
        status = await self.get_status()
        return status.power_consumption_watt

    @staticmethod
    def _validate_temperature(temperature: float) -> None:
        """
        Validate temperature is within acceptable range (0-30°C).

        Args:
            temperature: Temperature in Celsius to validate

        Raises:
            StoneConnectValidationError: If temperature is outside the 0-30°C range
        """
        if temperature < 0:
            raise StoneConnectValidationError(
                f"Temperature {temperature}°C is below minimum limit of 0°C"
            )
        if temperature > 30:
            raise StoneConnectValidationError(
                f"Temperature {temperature}°C is above maximum limit of 30°C"
            )

    @staticmethod
    def _is_power_mode(mode: OperationMode) -> bool:
        """Check if a mode is a power mode (HIGH, MEDIUM, LOW)."""
        return mode in [OperationMode.HIGH, OperationMode.MEDIUM, OperationMode.LOW]

    @staticmethod
    def _is_preset_mode(mode: OperationMode) -> bool:
        """Check if a mode is a preset mode (COMFORT, ECO, ANTIFREEZE)."""
        return mode in [
            OperationMode.COMFORT,
            OperationMode.ECO,
            OperationMode.ANTIFREEZE,
        ]

    @staticmethod
    def _is_custom_temperature_mode(mode: OperationMode) -> bool:
        """Check if a mode is a custom temperature mode (MANUAL, BOOST)."""
        return mode in [OperationMode.MANUAL, OperationMode.BOOST]

    def _get_preset_setpoint(
        self, mode: OperationMode, device_info: Info
    ) -> Optional[float]:
        """Get the preset setpoint temperature for a given mode."""
        if mode == OperationMode.COMFORT:
            return device_info.comfort_setpoint
        elif mode == OperationMode.ECO:
            return device_info.eco_setpoint
        elif mode == OperationMode.ANTIFREEZE:
            return device_info.antifreeze_setpoint
        else:
            return None
