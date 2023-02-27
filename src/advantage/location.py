from typing import List, TYPE_CHECKING, Optional
from advantage.util.helpers import deep_update

if TYPE_CHECKING:
    from advantage.charger import Charger


class Location:
    """This class implements a location.

    This class allows type checking.

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
    output :

    """

    def __init__(
        self,
        name: str = "",
        location_type: str = "",  # TODO remove?
        chargers: Optional[List["Charger"]] = None,
        grid_info: Optional[dict] = None,
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
