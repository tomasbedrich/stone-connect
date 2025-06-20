"""Stone Connect Heater data models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


def parse_timestamp(timestamp: Optional[int]) -> Optional[datetime]:
    """Parse timestamp from milliseconds to datetime."""
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / 1000)


class OperationMode(Enum):
    """Heater operation modes based on device constants."""

    # Primary modes seen from device constants (may vary by device model)
    ANTIFREEZE = "ANF"
    BOOST = "BST"
    COMFORT = "CMF"
    ECO = "ECO"
    HIGH = "HIG"
    HOLIDAY = "HOL"
    LOW = "LOW"
    MANUAL = "MAN"
    MEDIUM = "MED"
    SCHEDULE = "SCH"
    STANDBY = "SBY"

    def is_power_mode(self) -> bool:
        """Check if this is a power-based mode (HIGH/MEDIUM/LOW)."""
        return self in {self.HIGH, self.MEDIUM, self.LOW}

    def is_preset_mode(self) -> bool:
        """Check if this is a preset temperature mode (COMFORT/ECO/ANTIFREEZE)."""
        return self in {self.COMFORT, self.ECO, self.ANTIFREEZE}

    def is_custom_mode(self) -> bool:
        """Check if this is a custom temperature mode (MANUAL/BOOST)."""
        return self in {self.MANUAL, self.BOOST}

    def get_preset_setpoint(self, device_info: "Info") -> Optional[float]:
        """Get the preset setpoint for this mode from device info."""
        if self == self.COMFORT:
            return device_info.comfort_setpoint
        elif self == self.ECO:
            return device_info.eco_setpoint
        elif self == self.ANTIFREEZE:
            return device_info.antifreeze_setpoint
        return None


class UseMode(Enum):
    """Use modes based on actual API responses."""

    SETPOINT = "SET"
    POWER = "POW"


@dataclass
class HolidaySettings:
    """Holiday mode settings."""

    holiday_start: Optional[datetime] = None
    holiday_end: Optional[datetime] = None
    operative_mode: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HolidaySettings":
        """Create HolidaySettings from dictionary."""
        return cls(
            holiday_start=parse_timestamp(data.get("Holiday_Start")),
            holiday_end=parse_timestamp(data.get("Holiday_End")),
            operative_mode=data.get("Operative_Mode"),
        )


@dataclass
class ScheduleSlot:
    """Schedule slot for weekly schedule."""

    hour: int
    minute: int
    set_point: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduleSlot":
        """Create ScheduleSlot from dictionary."""
        return cls(
            hour=data["hour"],
            minute=data["minute"],
            set_point=data["set_point"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hour": self.hour,
            "minute": self.minute,
            "set_point": self.set_point,
        }


@dataclass
class ScheduleDay:
    """One day of weekly schedule."""

    week_day: int  # 0=Monday, 6=Sunday
    schedule_slots: List[ScheduleSlot]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduleDay":
        """Create ScheduleDay from dictionary."""
        return cls(
            week_day=data["week_day"],
            schedule_slots=[
                ScheduleSlot.from_dict(slot) for slot in data.get("schedule_slots", [])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "week_day": self.week_day,
            "schedule_slots": [slot.to_dict() for slot in self.schedule_slots],
        }


@dataclass
class Info:
    """Device information structure based on /info endpoint."""

    client_id: Optional[str] = None
    operative_mode: Optional[OperationMode] = None
    set_point: Optional[float] = None
    use_mode: Optional[UseMode] = None
    home_id: Optional[int] = None
    zone_id: Optional[int] = None
    appliance_id: Optional[int] = None
    temperature_unit: Optional[str] = None
    is_installed: Optional[bool] = None
    comfort_setpoint: Optional[float] = None
    eco_setpoint: Optional[float] = None
    antifreeze_setpoint: Optional[float] = None
    boost_timer: Optional[int] = None
    high_power: Optional[int] = None
    medium_power: Optional[int] = None
    low_power: Optional[int] = None
    mac_address: Optional[str] = None
    pcb_pn: Optional[str] = None
    pcb_version: Optional[str] = None
    fw_pn: Optional[str] = None
    fw_version: Optional[str] = None
    holiday: Optional[HolidaySettings] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    gps_precision: Optional[int] = None
    set_timezone: Optional[int] = None
    load_size_watt: Optional[int] = None
    home_name: Optional[str] = None
    zone_name: Optional[str] = None
    appliance_name: Optional[str] = None
    appliance_pn: Optional[str] = None
    appliance_sn: Optional[str] = None
    housing_pn: Optional[str] = None
    housing_sn: Optional[str] = None
    last_update: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Info":
        """Create Info from API response dictionary."""
        try:
            operative_mode = OperationMode(data.get("Operative_Mode"))
        except ValueError:
            operative_mode = None

        try:
            use_mode = UseMode(data.get("Use_Mode"))
        except ValueError:
            use_mode = None

        holiday_data = data.get("Holiday")
        holiday = HolidaySettings.from_dict(holiday_data) if holiday_data else None

        return cls(
            client_id=data.get("Client_ID"),
            operative_mode=operative_mode,
            set_point=data.get("Set_Point"),
            use_mode=use_mode,
            home_id=data.get("Home_ID"),
            zone_id=data.get("Zone_ID"),
            appliance_id=data.get("Appliance_ID"),
            temperature_unit=data.get("Temperature_Unit"),
            is_installed=data.get("Is_Installed"),
            comfort_setpoint=data.get("Comfort_Setpoint"),
            eco_setpoint=data.get("Eco_Setpoint"),
            antifreeze_setpoint=data.get("Antifreeze_Setpoint"),
            boost_timer=data.get("Boost_Timer"),
            high_power=data.get("High_Power"),
            medium_power=data.get("Medium_Power"),
            low_power=data.get("Low_Power"),
            mac_address=data.get("MAC_Address"),
            pcb_pn=data.get("PCB_PN"),
            pcb_version=data.get("PCB_Version"),
            fw_pn=data.get("FW_PN"),
            fw_version=data.get("FW_Version"),
            holiday=holiday,
            latitude=data.get("Latitude"),
            longitude=data.get("Longitude"),
            altitude=data.get("Altitude"),
            gps_precision=data.get("GPS_Precision"),
            set_timezone=data.get("Set_Timezone"),
            load_size_watt=data.get("Load_Size_Watt"),
            home_name=data.get("Home_Name"),
            zone_name=data.get("Zone_Name"),
            appliance_name=data.get("Appliance_Name"),
            appliance_pn=data.get("Appliance_PN"),
            appliance_sn=data.get("Appliance_SN"),
            housing_pn=data.get("Housing_PN"),
            housing_sn=data.get("Housing_SN"),
            last_update=parse_timestamp(data.get("Last_Update")),
        )


@dataclass
class Status:
    """Device status structure based on /Status endpoint."""

    client_id: Optional[str] = None
    set_point: Optional[float] = None
    operative_mode: Optional[OperationMode] = None
    power_consumption_watt: Optional[int] = None
    daily_energy: Optional[int] = None
    error_code: Optional[int] = None
    lock_status: Optional[bool] = None
    rssi: Optional[int] = None
    connected_to_broker: Optional[bool] = None
    broker_enabled: Optional[bool] = None
    last_update: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Status":
        """Create Status from API response dictionary."""
        try:
            operative_mode = OperationMode(data.get("Operative_Mode"))
        except ValueError:
            operative_mode = None

        return cls(
            client_id=data.get("Client_ID"),
            set_point=data.get("Set_Point"),
            operative_mode=operative_mode,
            power_consumption_watt=data.get("Power_Consumption_Watt"),
            daily_energy=data.get("Daily_Energy"),
            error_code=data.get("Error_Code"),
            lock_status=data.get("Lock_Status"),
            rssi=data.get("RSSI"),
            connected_to_broker=data.get("Connected_To_Broker"),
            broker_enabled=data.get("Broker_Enabled"),
            last_update=parse_timestamp(data.get("Last_Update")),
        )


@dataclass
class Schedule:
    """Weekly schedule structure based on /Schedule endpoint."""

    client_id: Optional[str] = None
    weekly_schedule: Optional[List[ScheduleDay]] = None
    last_update: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Create Schedule from API response dictionary."""
        weekly_schedule = None
        if "Weekly_Schedule" in data:
            weekly_schedule = [
                ScheduleDay.from_dict(day) for day in data["Weekly_Schedule"]
            ]

        return cls(
            client_id=data.get("Client_ID"),
            weekly_schedule=weekly_schedule,
            last_update=parse_timestamp(data.get("Last_Update")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result: Dict[str, Any] = {"Client_ID": self.client_id}
        if self.weekly_schedule:
            result["Weekly_Schedule"] = [day.to_dict() for day in self.weekly_schedule]
        return result
