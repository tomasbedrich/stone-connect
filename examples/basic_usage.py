#!/usr/bin/env python3
"""
Example script demonstrating Stone Connect Heater API usage.

This script shows how to use the stone_connect_heater library to:
- Connect to a heater
- Read device information and status
- Control temperature and operation mode
- Handle errors properly

Usage:
    python example.py <heater_ip> [--port PORT]

Example:
    python example.py 192.168.1.99
    python example.py 127.0.0.1 --port 8443
"""

import argparse
import asyncio
import logging

from stone_connect import (
    StoneConnectError,
    StoneConnectHeater,
)


async def basic_example(heater_ip: str, port: int = 443):
    """Basic usage example."""
    print(f"Connecting to heater at {heater_ip}:{port}...")

    # Connect to heater
    async with StoneConnectHeater(heater_ip, port=port) as heater:
        try:
            # Get device information
            print("\n📋 Device Information:")
            info = await heater.get_info()
            print(f"  Client ID: {info.client_id}")
            print(f"  Appliance Name: {info.appliance_name}")
            print(f"  Zone Name: {info.zone_name}")
            print(f"  Home Name: {info.home_name}")
            print(f"  MAC Address: {info.mac_address}")
            print(f"  FW Version: {info.fw_version}")
            print(f"  PCB Version: {info.pcb_version}")

            # Get current status
            print("\n🌡️  Current Status:")
            status = await heater.get_status()
            print(f"  Set Point: {status.set_point}°C")
            print(f"  Operation Mode: {status.operative_mode}")
            print(f"  Power Consumption: {status.power_consumption_watt}W")
            print(f"  Daily Energy: {status.daily_energy}")
            print(f"  Signal Strength: {status.rssi} dBm")
            print(f"  Error Code: {status.error_code}")
            print(f"  Lock Status: {status.lock_status}")

            # Example: Set manual temperature to 21°C
            print("\n🔧 Setting manual temperature to 21°C...")
            await heater.set_manual_temperature(21.0)

            # Example: Set to comfort mode (uses preset temperature)
            print("🔧 Setting to comfort mode...")
            await heater.set_comfort_mode()

            # Example: Set to eco mode (uses preset temperature)
            print("🔧 Setting to eco mode...")
            await heater.set_eco_mode()

            # Example: Set to high power mode (no temperature setpoint)
            print("🔧 Setting to high power mode...")
            await heater.set_standby()

            # Get updated status
            print("\n🌡️  Updated Status:")
            status = await heater.get_status()
            print(f"  Set Point: {status.set_point}°C")
            print(f"  Operation Mode: {status.operative_mode}")
            print(f"  Power Consumption: {status.power_consumption_watt}W")
            print(f"  Is Heating: {await heater.is_heating()}")

            # Get weekly schedule
            print("\n📅 Weekly Schedule:")
            schedule = await heater.get_schedule()
            if schedule.weekly_schedule:
                for day in schedule.weekly_schedule[:2]:  # Show first 2 days
                    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    print(f"  {day_names[day.week_day]}:")
                    for point in day.schedule_points:
                        print(
                            f"    {point.hour:02d}:{point.minute:02d} -> {point.set_point}°C"
                        )

            # Check if device supports power measurement
            print("\n" + "=" * 50)
            print("POWER MEASUREMENT CAPABILITY")
            print("=" * 50)

            has_power_support = await heater.has_power_measurement_support()
            print(f"Power measurement supported: {has_power_support}")

            if not has_power_support:
                print("⚠️  This device model/PCB may not support power measurement")
                print("   Power_Consumption_Watt will likely always be 0")
            else:
                print("✓  Device appears to support power measurement")

            print("\n✅ Example completed successfully!")

        except StoneConnectError as e:
            print(f"❌ Heater error: {e}")


async def monitoring_example(heater_ip: str, port: int = 443):
    """Example of continuous monitoring."""
    print(f"\n🔄 Starting monitoring of heater at {heater_ip}:{port}...")
    print("Press Ctrl+C to stop")

    async with StoneConnectHeater(heater_ip, port=port) as heater:
        try:
            while True:
                status = await heater.get_status()

                print(
                    f"\r🌡️  {status.set_point}°C "
                    f"({status.operative_mode.value if status.operative_mode else 'unknown'}) "
                    f"{'🔥' if (status.power_consumption_watt or 0) > 0 else '❄️ '} "
                    f"{status.power_consumption_watt or 0}W",
                    end="",
                )

                await asyncio.sleep(5)  # Update every 5 seconds

        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped")
        except StoneConnectError as e:
            print(f"\n❌ Heater error: {e}")


async def quick_check_example(heater_ip: str, port: int = 443):
    """Quick status check example."""
    print(f"\n⚡ Quick status check for {heater_ip}:{port}:")

    try:
        async with StoneConnectHeater(heater_ip, port=port) as heater:
            status = await heater.get_status()
        print(f"  Set Point: {status.set_point}°C")
        print(
            f"  Mode: {status.operative_mode.value if status.operative_mode else 'unknown'}"
        )
        print(f"  Power: {status.power_consumption_watt or 0}W")
        print(
            f"  Heating: {'Yes' if (status.power_consumption_watt or 0) > 0 else 'No'}"
        )
    except StoneConnectError as e:
        print(f"  ❌ Error: {e}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Stone Connect Heater Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python example.py 192.168.1.94
  python example.py 192.168.1.94 --port 8443
  python example.py 192.168.1.94 -p 80
        """,
    )

    parser.add_argument("heater_ip", help="IP address or hostname of the heater")

    parser.add_argument(
        "-p", "--port", type=int, default=443, help="HTTPS port (default: 443)"
    )

    args = parser.parse_args()

    print("🏠 Stone Connect Heater Example")
    print("=" * 40)
    print(f"Target: {args.heater_ip}:{args.port}")
    print()

    # Run basic example
    await basic_example(args.heater_ip, args.port)

    # Run quick check example
    await quick_check_example(args.heater_ip, args.port)

    # Ask if user wants to start monitoring
    try:
        response = input("\nStart continuous monitoring? (y/N): ").lower()
        if response in ["y", "yes"]:
            await monitoring_example(args.heater_ip, args.port)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye! 👋")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
