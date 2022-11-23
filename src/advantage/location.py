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
    output :

    """

    def __init__(
        self,
        name: str = "",
        location_type: str = "",
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

    def get_scenario_info(self, point_id: str, plug_types: List[str]):
        """This method matches all the ChargingPoints in the location with the given ChargingPoint ID.

        Parameters
        ----------
        point_id : str
            PointCharging ID that is sought-after in the location.
        plug_types : list[str]
            Available Plugs for the ChargingPoint.

        Returns
        -------
        dict
            Dictionary with all matching ChargingPoints in the location.

        """

        power = self.grid_info["power"] if self.grid_info else 0
        scenario_dict = {
            "constants": {
                "grid_connectors": {
                    "GC1": {"max_power": power, "cost": {"type": "fixed", "value": 0.3}}
                }
            }
        }
        for ch in self.chargers:
            info = ch.get_scenario_info(point_id, plug_types)
            deep_update(scenario_dict, info)
        return scenario_dict
