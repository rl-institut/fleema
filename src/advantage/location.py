from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from advantage.charger import Charger


class Location:
    """
    Location object contains name, type and various properties
    name:               location name
    type:               location type. "depot", "station", ...
    chargers:           list of chargers at the location
    grid_info:          dict with grid connection, load and generator time series, ...
    """
    def __init__(self,
                 location_name: str = "",
                 location_type: str = "",
                 chargers: Optional[List["Charger"]] = None,
                 grid_info: Optional[dict] = None
                 ):
        self.name = location_name
        self.type = location_type
        self.chargers = chargers if chargers else []
        self.grid_info = grid_info
        self.output = None

    @property
    def num_chargers(self):
        return len(self.chargers)

    @property
    def grid_connection(self):
        # TODO check if grid power > 0
        return isinstance(self.grid_info, dict)

    @property
    def available(self):
        return None

    @property
    def scenario_info(self):
        scenario_dict = {
            "constants": {
                "grid_connectors": {
                    "GC1": {
                        "max_power": self.grid_info["max_power"],
                        "cost": {
                            "type": "fixed",
                            "value": 0.3
                        }
                    }
                },
                # TODO for charger in self.chargers: deep_update(scenario_dict, charger.scenario_info)
                "charging_stations": {
                    "CS_sprinter_0": {
                        "max_power": 11,
                        "min_power": 0,
                        "parent": "GC1"
                    },
                    "CS_golf_0": {
                        "max_power": 22,
                        "min_power": 0,
                        "parent": "GC1"
                    }
                }
            }
        }
        return scenario_dict
