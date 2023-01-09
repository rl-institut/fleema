from enum import Enum


class Status(Enum):
    """Used for vehicle-statuses and task-types."""
    DRIVING = "driving"
    PARKING = "parking"
    CHARGING = "charging"
    BREAK = "break"
