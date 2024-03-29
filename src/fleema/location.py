from typing import List, TYPE_CHECKING, Optional
import pandas as pd
import numpy as np


from fleema.util.helpers import deep_update
from fleema.event import Status

if TYPE_CHECKING:
    from fleema.charger import Charger
    from fleema.event import Task


class Location:
    """This class implements a location.

    This class allows type checking.

    Attributes
    ----------
    name : str
        Name/ID of the location.
    location_type : str
        Location type can be "depot", "station", etc.
    chargers : list, optional
        List of chargers at the given location.
    grid_info : dict, optional
        Dictionary with grid connection in kW, load and generator time series.
        Example: {"power": 50, "load": load_df, "generator": gen_df}
    output : dict
        Comprises information on grid power and connected vehicles in total and for every charging point.


    """

    def __init__(
        self,
        name: str = "",
        location_type: str = "",  # TODO remove?
        chargers: Optional[List["Charger"]] = None,
        grid_info: Optional[dict] = None,
        event_csv: Optional[bool] = True,
    ):
        """
        Constructor of the Location class.

        Parameters
        ----------
        name : str
            Name/ID of the location.
        location_type : str
            Location type can be "depot", "station", etc.
        chargers : list, optional
            List of chargers at the given location.
        grid_info : dict, optional
            Dictionary with grid connection in kW, load and generator time series.
            Example: {"power": 50, "load": load_df, "generator": gen_df}

        """
        self.name = name
        self.location_type = location_type
        self.chargers = chargers if chargers else []
        self.grid_info = grid_info
        self.output = None
        self.event_csv = event_csv
        self.generator_exists = False
        self.occupation = pd.DataFrame()

    @property
    def num_chargers(self):
        """This get method returns the number of chargers at the location instance.

        Returns
        -------
            int
                Number of chargers.

        """
        return len(self.chargers)

    @property
    def grid_connection(self):
        """This method checks if the grid power is above zero.

        Returns
        -------
            bool
                Returns True if grid power is over zero and False if not.

        """
        # TODO check if grid power > 0
        return isinstance(self.grid_info, dict)

    @property
    def available(self):
        """This methods checks availability."""
        return None

    def init_occupation(self, time_steps):
        """Creates empty occupation DataFrame."""
        self.occupation = pd.DataFrame(
            0,
            index=np.arange(time_steps),
            columns=["total"],  # [c.name for c in self.chargers]
        )

    def set_power(self, power: float):
        """Set power of grid connector at this location."""
        if self.grid_info is None:
            self.grid_info = {}
        self.grid_info["power"] = power

    def set_generator(self, generator_dict):
        """Set generator infos for this location."""
        self.generator_dict = generator_dict
        self.generator_dict["grid_connector_id"] = "GC1"
        self.generator_exists = True

    def add_occupation_from_event(self, charging_event: "Task"):
        """Add occupation data from a given charging event."""
        if charging_event.task == Status.CHARGING:
            self.add_occupation(
                charging_event.start_time, charging_event.end_time, "total"
            )

    def add_occupation(self, start_time, end_time, column_name="total"):
        """Add occupation data."""
        try:
            self.occupation.loc[start_time:end_time, column_name] += 1
        except KeyError:
            print(
                "Warning: Invalid column name or index range when tracking occupation."
            )

    def is_available(self, start_time, end_time, column_name="total"):
        """Check if occupation in given time frame reaches the maximum. Returns True if time slot is available"""
        try:
            values_in_range = self.occupation.loc[start_time:end_time, column_name]
            return (values_in_range < self.num_chargers).all()
        except KeyError:
            print("Invalid column name or index range.")

    def get_scenario_info(self, plug_types: List[str], point_id: Optional[str] = None):
        """Create SpiceEV scenario dict for this Location.

        Parameters
        ----------
        plug_types : list[str]
            Plug types that the charging vehicle is compatible with
        point_id : str, optional
            ID of a specific charging point

        Returns
        -------
        dict
            Dictionary with all matching ChargingPoints in the location.

        """

        power = self.grid_info["power"] if self.grid_info else 0
        scenario_dict = {
            "components": {
                "grid_connectors": {
                    "GC1": {
                        "max_power": power,
                        # "cost": {"type": "fixed", "value": 0.3},
                    }  # TODO change cost params
                },
            },
        }
        if self.generator_exists:
            scenario_dict["events"] = {
                "energy_feed_in": {"GC1 feed-in": self.generator_dict}
            }
        for ch in self.chargers:
            # create scenario dict for chosen point id or the point with the highest power
            if point_id is None:
                point_id = ""
                highest_power = 0
                for cp in ch.charging_points:
                    power = cp.get_power(plug_types)
                    if power > highest_power:
                        highest_power = power
                        point_id = cp.id
            info = ch.get_scenario_info(point_id, plug_types)
            deep_update(scenario_dict, info)

        return scenario_dict

    def update_output(
        self, start_time, end_time, step_size, time_steps, charging_power_list
    ):
        """Records newest output when it is called during the vehicle method charge().

        Parameters
        ----------
        start_time : int
            Starting step of charging
        end_time : int
            Excluded end step of charging
        step_size : int
            Charging time in steps
        time_steps : int
            Number of steps in the scenario
        charging_power_list : list
            Charging power for each step during the charging event

        """
        if not self.output:
            self.output = {
                f"{self.name}_total_power": [0 for _ in range(time_steps)],
                f"{self.name}_total_connected_vehicles": [0 for _ in range(time_steps)],
            }
            if self.num_chargers > 1:
                for charger in self.chargers:
                    self.output[f"{charger.name}_power"] = [
                        0 for _ in range(time_steps)
                    ]
                    self.output[f"{charger.name}_connected_vehicle"] = [
                        0 for _ in range(time_steps)
                    ]

        for current_time in range(start_time, end_time, step_size):
            if current_time > time_steps:
                print("Charging time is out of time schedule!")
                break
            charging_power = (
                0 if len(charging_power_list) == 0 else charging_power_list.pop(0)
            )
            if self.num_chargers > 1:
                self.output[f"{self.chargers[0].name}_power"][
                    current_time
                ] += charging_power
                self.output[f"{self.chargers[0].name}_connected_vehicle"][
                    current_time
                ] += 1
            self.output[f"{self.name}_total_power"][current_time] += charging_power
            self.output[f"{self.name}_total_connected_vehicles"][current_time] += 1
