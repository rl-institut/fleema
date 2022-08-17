from dataclasses import dataclass


@dataclass
class Charger:
    """
    Dataclass containing all information about a single charging station.
    name: str:              Name/ID of the station
    charging_points:list:   List with information about each charging point. One dictionary per charging point
                            [
                            {"plugs": ["Type2", "AC"], "plug_power": [22, 3.7],
                            "charging_type": ["conductive", "conductive"]},
                            {...}
                            ]
    """
    name: str
    charging_points: list

    @property
    def num_points(self) -> int:
        return len(self.charging_points)

    @property
    def scenario_info(self) -> dict:
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
