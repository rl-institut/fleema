import pandas as pd
from typing import TYPE_CHECKING
from dataclasses import dataclass, asdict
from enum import Enum

if TYPE_CHECKING:
    from advantage.location import Location


class Status(Enum):
    """Used for vehicle-statuses and task-types."""

    DRIVING = "driving"
    PARKING = "parking"
    CHARGING = "charging"
    BREAK = "break"


@dataclass
class Event:
    """Base event dataclass. Includes basic data and representation functions.

    Attributes
    ----------
    start_time : int
        Starting time step of the event.
    end_time : int
        End time step of the event.
    """

    start_time: int
    end_time: int

    @property
    def data_dict(self):
        return asdict(self)

    @property
    def dataframe(self):
        return pd.DataFrame.from_dict(self.data_dict)  # TODO test


@dataclass
class Task(Event):
    """Saves data for a charging, driving or break event.

    Attributes
    ----------
    start_point : int
        Starting time step of the event.
    end_point : int
        End time step of the event.
    task : Status
        Status (Enum): DRIVING, CHARGING, PARKING, BREAK.
    float_time : float
        Length of the task.
    delta_soc : float
        A positive delta_soc means charging, negative is consumption.
    consumption : float
        Energy drain of the task.
    level_of_loading : float
        Additional load the vehicle carries (from 0 to 1)
    """

    start_point: "Location"
    end_point: "Location"
    task: Status
    float_time: float = 0.0
    delta_soc: float = 0.0
    consumption: float = 0.0
    level_of_loading: float = 0.0

    @property
    def is_calculated(self):
        """Checks, if float_time and delta_soc have been set.

        Returns
        -------
        bool
        """
        return (
            self.float_time != 0.0 and self.delta_soc != 0.0 and self.consumption != 0.0
        )
