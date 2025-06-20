#!/usr/bin/env python3
"""
Test suite for Stone Connect heater temperature validation.
"""

from unittest.mock import AsyncMock, patch

import pytest

from stone_connect import Info, OperationMode, Status, StoneConnectHeater
from stone_connect.exceptions import StoneConnectValidationError


class TestTemperatureValidation:
    """Test temperature validation and limits."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    def test_validate_temperature_valid_range(self):
        """Test temperature validation for valid temperatures."""
        # Test minimum valid temperature
        StoneConnectHeater._validate_temperature(0.0)

        # Test maximum valid temperature
        StoneConnectHeater._validate_temperature(30.0)

        # Test temperatures in the middle
        StoneConnectHeater._validate_temperature(15.0)
        StoneConnectHeater._validate_temperature(20.5)
        StoneConnectHeater._validate_temperature(25.7)

    def test_validate_temperature_below_minimum(self):
        """Test temperature validation for temperatures below 0°C."""
        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature -1.0°C is below minimum limit of 0°C",
        ):
            StoneConnectHeater._validate_temperature(-1.0)

        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature -10.5°C is below minimum limit of 0°C",
        ):
            StoneConnectHeater._validate_temperature(-10.5)

    def test_validate_temperature_above_maximum(self):
        """Test temperature validation for temperatures above 30°C."""
        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature 31.0°C is above maximum limit of 30°C",
        ):
            StoneConnectHeater._validate_temperature(31.0)

        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature 50.5°C is above maximum limit of 30°C",
        ):
            StoneConnectHeater._validate_temperature(50.5)

    async def test_set_temperature_valid_range(self):
        """Test set_temperature with valid temperature range."""
        mock_status = Status(operative_mode=OperationMode.MANUAL)

        with patch.object(
            self.heater,
            "get_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            with patch.object(
                self.heater,
                "set_temperature_and_mode",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_set:
                # Test minimum valid temperature
                await self.heater.set_temperature(0.0, OperationMode.MANUAL)
                mock_set.assert_called_with(0.0, OperationMode.MANUAL)

                # Test maximum valid temperature
                await self.heater.set_temperature(30.0, OperationMode.MANUAL)
                mock_set.assert_called_with(30.0, OperationMode.MANUAL)

                # Test temperature in the middle
                await self.heater.set_temperature(21.5, OperationMode.MANUAL)
                mock_set.assert_called_with(21.5, OperationMode.MANUAL)

    async def test_set_temperature_invalid_range(self):
        """Test set_temperature with invalid temperature range."""
        # Test below minimum
        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature -5.0°C is below minimum limit of 0°C",
        ):
            await self.heater.set_temperature(-5.0, OperationMode.MANUAL)

        # Test above maximum
        with pytest.raises(
            StoneConnectValidationError,
            match="Temperature 35.0°C is above maximum limit of 30°C",
        ):
            await self.heater.set_temperature(35.0, OperationMode.MANUAL)

    async def test_set_manual_temperature_valid_range(self):
        """Test set_manual_temperature with valid temperature range."""
        with patch.object(
            self.heater, "set_temperature", new_callable=AsyncMock, return_value=True
        ) as mock_set:
            await self.heater.set_manual_temperature(22.0)
            mock_set.assert_called_with(22.0, OperationMode.MANUAL)

    async def test_set_manual_temperature_invalid_range(self):
        """Test set_manual_temperature with invalid temperature range."""
        # This should fail at the set_temperature level, so we need to patch the validation
        with patch.object(self.heater, "set_temperature") as mock_set:
            mock_set.side_effect = ValueError(
                "Temperature 40.0°C is above maximum limit of 30°C"
            )

            with pytest.raises(
                ValueError, match="Temperature 40.0°C is above maximum limit of 30°C"
            ):
                await self.heater.set_manual_temperature(40.0)

    async def test_set_temperature_and_mode_validation(self):
        """Test that set_temperature_and_mode validates temperature for non-power modes."""
        mock_device_info = Info(client_id="test_client")

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(self.heater, "_request", new_callable=AsyncMock):
                # Valid temperature should work
                await self.heater.set_temperature_and_mode(20.0, OperationMode.MANUAL)

                # Invalid temperature should fail
                with pytest.raises(
                    StoneConnectValidationError,
                    match="Temperature 35.0°C is above maximum limit",
                ):
                    await self.heater.set_temperature_and_mode(
                        35.0, OperationMode.MANUAL
                    )

    async def test_set_temperature_and_mode_power_mode_no_validation(self):
        """Test that set_temperature_and_mode doesn't validate temperature for power modes."""
        mock_device_info = Info(client_id="test_client")

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(self.heater, "_request", new_callable=AsyncMock):
                # Power mode should work even with invalid temperature (temperature is ignored)
                await self.heater.set_temperature_and_mode(999.0, OperationMode.HIGH)

    async def test_set_operation_mode_with_preset_temperatures(self):
        """Test that set_operation_mode works with preset temperatures within range."""
        mock_device_info = Info(
            client_id="test_client",
            comfort_setpoint=19.0,  # Valid
            eco_setpoint=15.0,  # Valid
            antifreeze_setpoint=7.0,  # Valid
        )

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(
                self.heater,
                "set_temperature_and_mode",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_set:
                # Test comfort mode
                await self.heater.set_operation_mode(OperationMode.COMFORT)
                mock_set.assert_called_with(19.0, OperationMode.COMFORT)

                # Test eco mode
                await self.heater.set_operation_mode(OperationMode.ECO)
                mock_set.assert_called_with(15.0, OperationMode.ECO)

                # Test antifreeze mode
                await self.heater.set_operation_mode(OperationMode.ANTIFREEZE)
                mock_set.assert_called_with(7.0, OperationMode.ANTIFREEZE)

    async def test_set_operation_mode_with_invalid_preset_temperatures(self):
        """Test that set_operation_mode fails with invalid preset temperatures."""
        # Test with preset temperature above maximum
        mock_device_info = Info(
            client_id="test_client",
            comfort_setpoint=35.0,  # Invalid - above 30°C
        )

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with pytest.raises(
                StoneConnectValidationError,
                match="Temperature 35.0°C is above maximum limit",
            ):
                await self.heater.set_operation_mode(OperationMode.COMFORT)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
