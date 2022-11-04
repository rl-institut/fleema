from dataclasses import dataclass
from typing import List, Dict, Optional

from advantage.util.helpers import deep_update


@dataclass
class PlugType:
    """Class implements any type of plug given the parameters.

    Attributes
    ----------
    name : str
    capacity : float
    charging_type : list[str], optional

    """
    name: str
    capacity: float
    charging_type: Optional[str] = None


@dataclass
class ChargingPoint:
    """Dataclass containing all information about a single charging point.

    Attributes
    ----------
    id : str
        Identifier of this charging point.
    plugs : list[str]
        List of available plugs.
    power : list[float]
        List of maximum power per plug.
    type : str
        Charging type (conductive, inductive, ...).

    """
    id: str
    plugs: List["PlugType"]

    def get_power(self, plug_types: List[str]):  # TODO maybe give list of PlugType instead
        """Returns max power for a specific plug type (0 if the plug doesn't exist at this point)"""
        max_power = 0.
        for plug in self.plugs:
            if plug.name not in plug_types:
                continue
            else:
                power = plug.capacity
                max_power = power if power > max_power else max_power
        return max_power


class Charger:
    """Dataclass that implements charger which can interact with ChargingPoints and their plugs.

    Attributes
    ----------
    name : str
        Name/ID of the station.
    charging_points : list
        List of charging points.

    """
    def __init__(self, name: str, charging_points: List["ChargingPoint"]) -> None:
        self.name = name
        self.charging_points = charging_points

    @property
    def num_points(self) -> int:
        return len(self.charging_points)

    def get_scenario_info(self, point_id: str, plug_types: List[str]) \
            -> Dict[str, Dict[str, Dict[str, Dict[str, object]]]]:
        """This method checks if Charger and the given charging point ID match.

        Returns
        -------
        dict
            Dictionary with all available charging points.

        Raises
        ------
        ValueError
            If point_id doesn't match any possible ChargingPoints in the Charger instance.
        ValueError
             If Charger doesn't have any charging points.

        """

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

    @classmethod
    def from_json(cls, name, number_charging_points: int, plug_types: list):
        """This classmethod returns an instance of Charger with an initialized charging_points attribute."""
        cp_list = []
        for i in range(number_charging_points):
            cp_list.append(ChargingPoint(f"{name}_{i}", plug_types))
        return Charger(name, cp_list)
