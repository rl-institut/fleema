from dataclasses import dataclass, field

from typing import List

from advantage.charger import Charger


@dataclass
class Location:
    """
    Location object contains id, type and various properties
    """
    location_id: str = ""
    status: str = "available"
    type: str = "hpc"
    chargers: List["Charger"] = field(default_factory=list)
    grid_info: dict = None
    output = None

    def has_charger(self):
        return len(self.chargers)

    def has_grid_connection(self):
        # TODO check if grid power > 0
        return isinstance(self.grid_info, dict)

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
                # TODO for charger in self.chargers: scenario_dict.update(charger.scenario_info)
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
