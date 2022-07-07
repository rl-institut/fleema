from dataclasses import dataclass

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from advantage.vehicle import Vehicle


@dataclass
class Charger:
    name: str = ""
    connected_vehicle: Optional["Vehicle"] = None
    # TODO: add charger info

    @property
    def scenario_info(self):
        scenario_dict = {
            "constants": {
                "charging_stations": {
                    self.name: {
                        # TODO add charger info
                        "max_power": 11,
                        "min_power": 0,
                        "parent": "GC1"
                    }
                }
            }
        }
        return scenario_dict
