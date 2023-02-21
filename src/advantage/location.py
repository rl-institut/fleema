import pandas as pd
import pathlib
from typing import List, TYPE_CHECKING, Optional
from advantage.util.helpers import deep_update

if TYPE_CHECKING:
    from advantage.charger import Charger


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
    TODO
    output : dict
        Dictionary with


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
        self.generator_exists = False

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

    def update_output(self, start_time, charging_time, charging_power):
        """Records newest output when it is called during the vehicle method charge().

        TODO
        Parameters
        ----------
        start_time : str
        charging_time : int
        charging_power : float
        directory : :obj:`pathlib.Path`
            Save directory

        """
        current_time = pd.Timestamp(start_time)
        for i in range(charging_time):
            x = pd.Timedelta(hours=i)
            current_time = current_time - x

            if current_time not in self.output:
                self.output[current_time] = {}
                self.output[current_time]['total_power'] = charging_power
                self.output[current_time]['total_connected_vehicles'] = 1
                self.output[current_time][f'{self.name}_connected_vehicles'] = 1
            else:
                self.output[current_time]['total_power'] += charging_power
                self.output[current_time]['total_connected_vehicles'] += 1
                self.output[current_time][f'{self.name}_connected_vehicles'] += 1
            self.output[current_time][f'{self.name}_power'] = charging_power

        if self.event_csv:

            total_power = []
            total_connected_vehicles = []
            individual_power = []
            individual_cv = []
            for k, v in self.output.items():
                total_power.append(v['total_power'])
                total_connected_vehicles.append(v['total_connected_vehicles'])
                individual_power.append(v[f'{self.name}_power'])
                individual_cv.append(v[f'{self.name}_connected_vehicles'])

            activity = pd.DataFrame({
                    'timestamp': self.output.keys(),
                    'total_power': total_power,
                    f'{self.name}_power': individual_power,
                    f'{self.name}_connected_vehicles': individual_cv,
            })
            activity = activity.reset_index(drop=True)
            activity.to_csv(pathlib.Path(f"{self.name}_grid_timeseries.csv"))
