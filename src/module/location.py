from dataclasses import dataclass


@dataclass
class Location:
    """
    Location object contains id, type and various properties
    """
    location_id: str
    status: str
    type: str
    charger_properties: dict = None
    grid_info: dict = None
    output = None

    def has_charger(self):
        return isinstance(self.charger_properties, dict)

    def has_grid_connection(self):
        return isinstance(self.grid_info, dict)
