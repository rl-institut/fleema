from dataclasses import dataclass


class Vehicle:
    """
    The vehicle contains tech parameters as well as tasks.
    Functions:
        charge
        drive
    """

    def __init__(self,
                 vehicle_type: object,
                 status: str,
                 soc: float,
                 availability: bool,
                 rotation: str = None,
                 current_location: object = None
                 ):
        self.vehicle_type = vehicle_type
        self.status = status
        self.soc = soc
        self.availability = availability
        self.rotation = rotation
        self.current_location = current_location
        self.output = None
        self.task = None

    def charge(self):
        # call spiceev charging depending on soc, location, task
        return

    def drive(self):
        # call drive api with task, soc, ...
        return


@dataclass
class VehicleType:
    """
    The VehicleType contains static vehicle data.
    name:               type name
    capacity:           battery capacity in kWh
    base_consumption:        in kWh/km ?
    charging_curve:     example: [[0, 50], [0.8, 50], [1, 20]], first number is SoC, second the
                        possible max power
    min_charging_power: least amount of charging power possible, as a share of max power
    """
    name: str
    capacity: float
    base_consumption: float
    charging_curve: list
    min_charging_power: float


# example inherited class as proof of concept, remove later if unused
@dataclass
class BusType(VehicleType):
    max_passenger_number: int
