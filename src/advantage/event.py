import pandas as pd
from typing import TYPE_CHECKING
from dataclasses import dataclass, asdict

if TYPE_CHECKING:
    from advantage.location import Location


@dataclass
class Event:
    """
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
    """
    Attributes
    ----------
    start_time : int
        Starting time step of the event.
    end_time : int
        End time step of the event.
    departure_point : Location
        Starting point of the task.
    arrival_point : Location
        End point of the task.
    task : str
        Task type: driving, charging, parking, break.
    delta_soc : float
        A positive delta_soc means charging, negative is consumption.
    """

    start_point: "Location"
    end_point: "Location"
    task: str  # TODO enum
    float_time: float = 0.0
    delta_soc: float = 0.0

    @property
    def is_calculated(self):
        """
        Checks, if float_time and delta_soc have been set.

        Returns
        -------
        bool
        """
        return self.float_time != 0.0 and self.delta_soc != 0.0
