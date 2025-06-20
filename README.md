# Stone Connect Heater Python Library

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An async Python library for controlling Stone Connect WiFi electric heaters via their local HTTPS API.

## Features

- **Async/await support** - Built with modern Python async patterns
- **Local API communication** - Direct connection to your heater without cloud dependency
- **Comprehensive control** - Temperature, operation modes, schedules, and more
- **Type safety** - Full type hints and data validation
- **Easy integration** - Simple context manager interface
- **Robust error handling** - Detailed exception hierarchy
- **Well tested** - Comprehensive test suite with high coverage

## Supported Operations

- 🌡️ **Temperature Control** - Set target temperature and read current values
- 🔥 **Operation Modes** - Manual, Comfort, Eco, Antifreeze, Schedule, Boost, and power modes
- 📅 **Schedule Information** - Read weekly heating schedules
- 📊 **Status Monitoring** - Heater status and sensor readings
- ℹ️ **Device Information** - Hardware details, firmware version, network info

## Installation

```bash
pip install stone-connect
```

### Development Installation

```bash
git clone https://github.com/tomasbedrich/stone-connect.git
cd stone-connect
pip install -e ".[dev]"
```

## Quick Start

```python
import asyncio
from stone_connect import StoneConnectHeater, OperationMode

async def main():
    # Connect to your heater (replace with your heater's IP)
    async with StoneConnectHeater("192.168.1.100") as heater:
        # Get device information
        info = await heater.get_info()
        print(f"Connected to: {info.appliance_name}")
        
        # Get current status
        status = await heater.get_status()
        print(f"Current temperature: {status.current_temperature}°C")
        print(f"Target temperature: {status.set_point}°C")
        
        # Set temperature to 22°C in manual mode
        await heater.set_temperature(22.0, OperationMode.MANUAL)
        
        # Switch to comfort mode
        await heater.set_operation_mode(OperationMode.COMFORT)

if __name__ == "__main__":
    asyncio.run(main())
```

## Disclaimer

This library is not officially associated with Stone Connect or any heater manufacturer. It is developed through reverse engineering of the public API for personal and educational use. Use at your own risk.
