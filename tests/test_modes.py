#!/usr/bin/env python3
"""
Test suite for Stone Connect heater mode categorization and API functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest

from stone_connect import (
    Info,
    OperationMode,
    Status,
    StoneConnectHeater,
    UseMode,
    parse_timestamp,
)
from stone_connect.exceptions import StoneConnectValidationError


class TestModeCategorization:
    """Test mode categorization helper methods."""

    def test_power_modes(self):
        """Test power mode identification."""
        power_modes = [OperationMode.HIGH, OperationMode.MEDIUM, OperationMode.LOW]
        for mode in power_modes:
            assert StoneConnectHeater._is_power_mode(mode), (
                f"{mode} should be a power mode"
            )
            assert not StoneConnectHeater._is_preset_mode(mode), (
                f"{mode} should not be a preset mode"
            )
            assert not StoneConnectHeater._is_custom_temperature_mode(mode), (
                f"{mode} should not be a custom temperature mode"
            )

    def test_preset_modes(self):
        """Test preset mode identification."""
        preset_modes = [
            OperationMode.COMFORT,
            OperationMode.ECO,
            OperationMode.ANTIFREEZE,
        ]
        for mode in preset_modes:
            assert not StoneConnectHeater._is_power_mode(mode), (
                f"{mode} should not be a power mode"
            )
            assert StoneConnectHeater._is_preset_mode(mode), (
                f"{mode} should be a preset mode"
            )
            assert not StoneConnectHeater._is_custom_temperature_mode(mode), (
                f"{mode} should not be a custom temperature mode"
            )

    def test_custom_temperature_modes(self):
        """Test custom temperature mode identification."""
        custom_modes = [OperationMode.MANUAL, OperationMode.BOOST]
        for mode in custom_modes:
            assert not StoneConnectHeater._is_power_mode(mode), (
                f"{mode} should not be a power mode"
            )
            assert not StoneConnectHeater._is_preset_mode(mode), (
                f"{mode} should not be a preset mode"
            )
            assert StoneConnectHeater._is_custom_temperature_mode(mode), (
                f"{mode} should be a custom temperature mode"
            )

    def test_other_modes(self):
        """Test other modes (standby, schedule, holiday)."""
        other_modes = [
            OperationMode.STANDBY,
            OperationMode.SCHEDULE,
            OperationMode.HOLIDAY,
        ]
        for mode in other_modes:
            assert not StoneConnectHeater._is_power_mode(mode), (
                f"{mode} should not be a power mode"
            )
            assert not StoneConnectHeater._is_preset_mode(mode), (
                f"{mode} should not be a preset mode"
            )
            assert not StoneConnectHeater._is_custom_temperature_mode(mode), (
                f"{mode} should not be a custom temperature mode"
            )


class TestPresetSetpointRetrieval:
    """Test preset setpoint retrieval."""

    def setup_method(self):
        """Set up test fixtures."""
        self.device_info = Info(
            comfort_setpoint=19.0, eco_setpoint=15.0, antifreeze_setpoint=7.0
        )
        self.heater = StoneConnectHeater("127.0.0.1")  # Dummy IP for testing

    def test_comfort_setpoint(self):
        """Test comfort setpoint retrieval."""
        result = self.heater._get_preset_setpoint(
            OperationMode.COMFORT, self.device_info
        )
        assert result == 19.0

    def test_eco_setpoint(self):
        """Test eco setpoint retrieval."""
        result = self.heater._get_preset_setpoint(OperationMode.ECO, self.device_info)
        assert result == 15.0

    def test_antifreeze_setpoint(self):
        """Test antifreeze setpoint retrieval."""
        result = self.heater._get_preset_setpoint(
            OperationMode.ANTIFREEZE, self.device_info
        )
        assert result == 7.0

    def test_non_preset_modes(self):
        """Test that non-preset modes return None."""
        non_preset_modes = [
            OperationMode.MANUAL,
            OperationMode.HIGH,
            OperationMode.STANDBY,
        ]
        for mode in non_preset_modes:
            result = self.heater._get_preset_setpoint(mode, self.device_info)
            assert result is None

    def test_missing_setpoints(self):
        """Test behavior when setpoints are missing."""
        empty_device_info = Info()
        result = self.heater._get_preset_setpoint(
            OperationMode.COMFORT, empty_device_info
        )
        assert result is None


class TestDataStructures:
    """Test data structure parsing and validation."""

    def test_operation_mode_enum(self):
        """Test OperationMode enum values."""
        assert OperationMode.COMFORT.value == "CMF"
        assert OperationMode.ECO.value == "ECO"
        assert OperationMode.HIGH.value == "HIG"
        assert OperationMode.MANUAL.value == "MAN"
        assert OperationMode.STANDBY.value == "SBY"

    def test_use_mode_enum(self):
        """Test UseMode enum values."""
        assert UseMode.SETPOINT.value == "SET"
        assert UseMode.POWER.value == "POW"

    def test_device_info_creation(self):
        """Test Info dataclass creation."""
        device_info = Info(
            client_id="test_client",
            operative_mode=OperationMode.COMFORT,
            set_point=20.0,
            use_mode=UseMode.SETPOINT,
            comfort_setpoint=19.0,
        )
        assert device_info.client_id == "test_client"
        assert device_info.operative_mode == OperationMode.COMFORT
        assert device_info.set_point == 20.0
        assert device_info.use_mode == UseMode.SETPOINT
        assert device_info.comfort_setpoint == 19.0

    def test_device_status_creation(self):
        """Test Status dataclass creation."""
        status = Status(
            client_id="test_client",
            set_point=21.0,
            operative_mode=OperationMode.MANUAL,
            power_consumption_watt=1500,
        )
        assert status.client_id == "test_client"
        assert status.set_point == 21.0
        assert status.operative_mode == OperationMode.MANUAL
        assert status.power_consumption_watt == 1500

    def test_parse_timestamp(self):
        """Test timestamp parsing utility."""
        # Test valid timestamp (milliseconds)
        timestamp_ms = 1640995200000  # 2022-01-01 00:00:00 UTC
        result = parse_timestamp(timestamp_ms)
        assert result is not None
        assert result.year == 2022
        assert result.month == 1
        assert result.day == 1

        # Test None timestamp
        result = parse_timestamp(None)
        assert result is None


class TestHeaterAPI:
    """Test heater API methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    @pytest.fixture
    def mock_device_info(self):
        """Mock device info for testing."""
        return {
            "Client_ID": "test_client_123",
            "Operative_Mode": "CMF",
            "Set_Point": 20.0,
            "Use_Mode": "SET",
            "Comfort_Setpoint": 19.0,
            "Eco_Setpoint": 15.0,
            "Antifreeze_Setpoint": 7.0,
        }

    @pytest.fixture
    def mock_device_status(self):
        """Mock device status for testing."""
        return {
            "Client_ID": "test_client_123",
            "Set_Point": 20.0,
            "Operative_Mode": "CMF",
            "Power_Consumption_Watt": 1200,
        }

    async def test_set_manual_temperature_validation(self):
        """Test that set_temperature validates modes correctly."""
        # Test that power modes are rejected
        with pytest.raises(
            StoneConnectValidationError,
            match="Power mode.*doesn't use temperature setpoints",
        ):
            await self.heater.set_temperature(20.0, OperationMode.HIGH)

        # Test that preset modes are rejected
        with pytest.raises(
            StoneConnectValidationError,
            match="Preset mode.*uses predefined temperature",
        ):
            await self.heater.set_temperature(20.0, OperationMode.COMFORT)

    async def test_set_power_mode_validation(self):
        """Test that set_power_mode validates power modes correctly."""
        # Valid power mode should work (would need mocking for actual API call)
        with patch.object(
            self.heater, "set_operation_mode", new_callable=AsyncMock
        ) as mock_set_mode:
            await self.heater.set_power_mode(OperationMode.HIGH)
            mock_set_mode.assert_called_once_with(OperationMode.HIGH)

        # Invalid power mode should raise error
        with pytest.raises(
            StoneConnectValidationError, match="is not a valid power mode"
        ):
            await self.heater.set_power_mode(OperationMode.COMFORT)

    async def test_convenience_methods(self):
        """Test convenience methods delegate correctly."""
        with patch.object(
            self.heater, "set_operation_mode", new_callable=AsyncMock
        ) as mock_set_mode:
            await self.heater.set_comfort_mode()
            mock_set_mode.assert_called_with(OperationMode.COMFORT)

            await self.heater.set_eco_mode()
            mock_set_mode.assert_called_with(OperationMode.ECO)

            await self.heater.set_antifreeze_mode()
            mock_set_mode.assert_called_with(OperationMode.ANTIFREEZE)

            await self.heater.set_standby()
            mock_set_mode.assert_called_with(OperationMode.STANDBY)

        with patch.object(
            self.heater, "set_temperature", new_callable=AsyncMock
        ) as mock_set_temp:
            await self.heater.set_manual_temperature(22.0)
            mock_set_temp.assert_called_with(22.0, OperationMode.MANUAL)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
