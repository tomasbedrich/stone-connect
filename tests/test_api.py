#!/usr/bin/env python3
"""
Test suite for Stone Connect heater API responses and error handling.
"""

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from stone_connect import (
    Info,
    OperationMode,
    Status,
    StoneConnectHeater,
)
from stone_connect.exceptions import StoneConnectValidationError
from stone_connect.models import UseMode


class TestAPIResponseParsing:
    """Test API response parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    async def test_parse_device_info_response(self):
        """Test parsing device info response."""
        mock_response = {
            "Client_ID": "571519332SN20244900365",
            "Operative_Mode": "CMF",
            "Set_Point": 20.0,
            "Use_Mode": "SET",
            "Comfort_Setpoint": 19.0,
            "Eco_Setpoint": 15.0,
            "Antifreeze_Setpoint": 7.0,
            "MAC_Address": "30:c6:f7:e9:e2:48",
            "FW_Version": "1.2.3",
        }

        with patch.object(
            self.heater, "_request", new_callable=AsyncMock, return_value=mock_response
        ):
            device_info = await self.heater.get_info()

            assert device_info.client_id == "571519332SN20244900365"
            assert device_info.operative_mode == OperationMode.COMFORT
            assert device_info.set_point == 20.0
            assert device_info.use_mode == UseMode.SETPOINT
            assert device_info.comfort_setpoint == 19.0
            assert device_info.eco_setpoint == 15.0
            assert device_info.antifreeze_setpoint == 7.0
            assert device_info.mac_address == "30:c6:f7:e9:e2:48"
            assert device_info.fw_version == "1.2.3"

    async def test_parse_device_status_response(self):
        """Test parsing device status response."""
        mock_response = {
            "Client_ID": "571519332SN20244900365",
            "Set_Point": 21.5,
            "Operative_Mode": "MAN",
            "Power_Consumption_Watt": 1500,
            "Daily_Energy": 2500,
            "Error_Code": 0,
            "Lock_Status": False,
            "RSSI": -45,
            "Connected_To_Broker": True,
            "Broker_Enabled": True,
        }

        with patch.object(
            self.heater, "_request", new_callable=AsyncMock, return_value=mock_response
        ):
            status = await self.heater.get_status()

            assert status.client_id == "571519332SN20244900365"
            assert status.set_point == 21.5
            assert status.operative_mode == OperationMode.MANUAL
            assert status.power_consumption_watt == 1500
            assert status.daily_energy == 2500
            assert status.error_code == 0
            assert status.lock_status is False
            assert status.rssi == -45
            assert status.connected_to_broker is True
            assert status.broker_enabled is True

    async def test_parse_unknown_operation_mode(self):
        """Test handling of unknown operation modes."""
        mock_response = {
            "Client_ID": "test_client",
            "Operative_Mode": "UNKNOWN_MODE",
            "Set_Point": 20.0,
        }

        with patch.object(
            self.heater, "_request", new_callable=AsyncMock, return_value=mock_response
        ):
            # Should not crash but log a warning
            device_info = await self.heater.get_info()
            assert device_info.operative_mode is None  # Unknown mode becomes None

    async def test_parse_unknown_use_mode(self):
        """Test handling of unknown use modes."""
        mock_response = {
            "Client_ID": "test_client",
            "Use_Mode": "UNKNOWN_USE_MODE",
            "Set_Point": 20.0,
        }

        with patch.object(
            self.heater, "_request", new_callable=AsyncMock, return_value=mock_response
        ):
            # Should not crash but log a warning
            device_info = await self.heater.get_info()
            assert device_info.use_mode is None  # Unknown mode becomes None


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    async def test_connection_error_handling(self):
        """Test connection error handling."""
        with patch.object(
            self.heater,
            "_request",
            new_callable=AsyncMock,
            side_effect=aiohttp.ClientError("Connection failed"),
        ):
            with pytest.raises(
                aiohttp.ClientError
            ):  # Should raise the connection error
                await self.heater.get_info()

    async def test_invalid_json_response(self):
        """Test handling of invalid JSON responses."""
        # Mock a response that's not valid JSON structure for our parsing
        mock_response = {"unexpected": "structure"}

        with patch.object(
            self.heater, "_request", new_callable=AsyncMock, return_value=mock_response
        ):
            device_info = await self.heater.get_info()
            # Should handle gracefully with None values
            assert device_info.client_id is None

    async def test_set_operation_mode_with_missing_preset(self):
        """Test setting preset mode when device info is missing preset temperatures."""
        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=Info(client_id="test_client"),
        ):
            # Should raise StoneConnectValidationError when trying to set comfort mode without preset
            with pytest.raises(
                StoneConnectValidationError, match="No preset temperature found"
            ):
                await self.heater.set_operation_mode(OperationMode.COMFORT)


class TestAPIRequestBuilding:
    """Test API request building for different operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    async def test_set_power_mode_request(self):
        """Test that power mode requests don't include Set_Point."""
        mock_device_info = Info(client_id="test_client")

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(
                self.heater, "_request", new_callable=AsyncMock
            ) as mock_request:
                await self.heater.set_temperature_and_mode(25.0, OperationMode.HIGH)

                # Check that the request was called with the right parameters
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                assert call_args[0][0] == "PUT"  # method
                assert call_args[0][1] == "setpoint"  # endpoint

                request_body = call_args[0][2]  # body
                assert request_body["Client_ID"] == "test_client"
                assert request_body["Operative_Mode"] == "HIG"
                assert request_body["Set_Point"] == 0

    async def test_set_preset_mode_request(self):
        """Test that preset mode requests include the correct preset temperature."""
        mock_device_info = Info(client_id="test_client", comfort_setpoint=19.0)

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(
                self.heater, "_request", new_callable=AsyncMock
            ) as mock_request:
                await self.heater.set_operation_mode(OperationMode.COMFORT)

                # Check that the request was called with preset temperature
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                request_body = call_args[0][2]  # body
                assert request_body["Client_ID"] == "test_client"
                assert request_body["Operative_Mode"] == "CMF"
                assert (
                    request_body["Set_Point"] == 19.0
                )  # Should use preset temperature

    async def test_set_manual_mode_request(self):
        """Test that manual mode requests include the specified temperature."""
        mock_device_info = Info(client_id="test_client")

        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            with patch.object(
                self.heater, "_request", new_callable=AsyncMock
            ) as mock_request:
                await self.heater.set_temperature_and_mode(22.5, OperationMode.MANUAL)

                # Check that the request includes the specified temperature
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                request_body = call_args[0][2]  # body
                assert request_body["Client_ID"] == "test_client"
                assert request_body["Operative_Mode"] == "MAN"
                assert (
                    request_body["Set_Point"] == 22.5
                )  # Should use specified temperature


class TestConvenienceMethods:
    """Test convenience method functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.heater = StoneConnectHeater("127.0.0.1")

    async def test_is_heating_detection(self):
        """Test heating detection based on power consumption."""
        # Test heating (power > 0)
        mock_status = Status(operative_mode=OperationMode.MANUAL)
        with patch.object(
            self.heater,
            "get_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            is_heating = await self.heater.is_heating()
            assert is_heating is True

        # Test not heating (power = 0)
        mock_status = Status(operative_mode=OperationMode.STANDBY)
        with patch.object(
            self.heater,
            "get_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            is_heating = await self.heater.is_heating()
            assert is_heating is False

        # Test unknown (power = None)
        mock_status = Status(operative_mode=None)
        with patch.object(
            self.heater,
            "get_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            is_heating = await self.heater.is_heating()
            assert is_heating is None

    async def test_get_signal_strength(self):
        """Test signal strength retrieval."""
        mock_status = Status(rssi=-42)
        with patch.object(
            self.heater,
            "get_status",
            new_callable=AsyncMock,
            return_value=mock_status,
        ):
            signal_strength = await self.heater.get_signal_strength()
            assert signal_strength == -42

    async def test_get_current_temperature(self):
        """Test current temperature retrieval."""
        mock_device_info = Info(set_point=21.5)
        with patch.object(
            self.heater,
            "get_info",
            new_callable=AsyncMock,
            return_value=mock_device_info,
        ):
            temp = await self.heater.get_current_temperature()
            assert temp == 21.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
