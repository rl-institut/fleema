from dataclasses import dataclass
from typing import List, Dict

from advantage.util.helpers import deep_update


@dataclass
class ChargingPoint:
    """
    Dataclass containing all information about a single charging point.
    id: str:            identifier of this charging point
    plugs: list[str]:   list of available plugs
    power: list[float]: list of max power per plug
    type: str:          charging type (conductive, inductive, ...)
    """
    id: str
    plugs: list
    power: list
    type: str

    def get_power(self, plug_types: List[str]):
        """Returns max power for a specific plug type (0 if the plug doesn't exist at this point)"""
        max_power = 0
        for plug_type in plug_types:
            if plug_type not in self.plugs:
                break
            else:
                idx = self.plugs.index(plug_type)
                power = self.power[idx]
                if power > max_power:
                    max_power = power
        return max_power


@dataclass
class Charger:
    """
    Dataclass containing all information about a single charging station.
    name: str:              Name/ID of the station
    charging_points:list:   List of ChargingPoints
    """
    name: str
    charging_points: List["ChargingPoint"]

    @property
    def num_points(self) -> int:
        return len(self.charging_points)

    def get_scenario_info(self, point_id: str, plug_types: List[str]) \
            -> Dict[str, Dict[str, Dict[str, Dict[str, object]]]]:
        if self.num_points:
            scenario_dict: Dict[str, Dict[str, Dict[str, Dict[str, object]]]] = {
                "constants": {
                    "charging_stations": {
                    }
                }
            }
            point_found = False
            for cp in self.charging_points:
                if cp.id == point_id:
                    point_found = True
                    cp_dict = {
                        "constants": {
                            "charging_stations": {
                                cp.id: {
                                    "max_power": cp.get_power(plug_types),
                                    "min_power": 0,
                                    "parent": "GC1"
                                }
                            }
                        }
                    }
                    deep_update(scenario_dict, cp_dict)
            if point_found:
                return scenario_dict
            else:
                raise ValueError(f"Point ID {point_id} doesn't match any Points in charger {self.name}")
        else:
            raise ValueError(f"Scenario dictionary requested of charger {self.name} with no charging points")
