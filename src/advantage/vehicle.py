from dataclasses import dataclass, field
from advantage.location import Location


@dataclass
class VehicleType:
    """
    The VehicleType contains static vehicle data.
    name:               vehicle type name
    battery_capacity:   battery capacity in kWh
    soc_min:            minimum state of charge that should remain in battery after a drive
    base_consumption:   in kWh/km ?
    charging_capacity:  dict containing values for fast (dc) and slow (ac) charging
    charging_curve:     example: [[0, 50], [0.8, 50], [1, 20]], first number is SoC, second the
                        possible max power
    min_charging_power: least amount of charging power possible, as a share of max power
    """
    name: str = "vehicle_name"
    battery_capacity: float = 50.
    soc_min: float = 0.
    base_consumption: float = 0.
    charging_capacity: dict = field(default_factory=dict)
    charging_curve: list = field(default_factory=list)
    min_charging_power: float = 0.
    label: str = None


# example inherited class as proof of concept, TODO remove later if unused
@dataclass
class BusType(VehicleType):
    max_passenger_number: int = 0


class Vehicle:
    """
    The vehicle contains tech parameters as well as tasks.
    Functions:
        charge
        drive
    """

    def __init__(self,
                 vehicle_type: "VehicleType" = VehicleType(),
                 status: str = "parking",
                 soc: float = 1,
                 availability: bool = True,
                 rotation: str = None,
                 current_location: "Location" = None
                 ):
        self.vehicle_type = vehicle_type
        self.status = status
        self.soc = soc
        self.availability = availability
        self.rotation = rotation
        self.current_location = current_location
        self.task = None

        self.output = {
            "timestamp": [],
            "event_start": [],
            "event_time": [],
            "location": [],
            "status": [],
            "soc": [],
            "charging_demand": [],
            "nominal_charging_capacity": [],
            "charging_power": [],
            "consumption": []
        }

    def _update_activity(self, timestamp, event_start, event_time, charging_power=0):
        """Records newest energy and activity"""
        self.soc = round(self.soc, 4)
        self.output["timestamp"].append(timestamp)
        self.output["event_start"].append(event_start)
        self.output["event_time"].append(event_time)
        self.output["location"].append(self.status)
        # self.output["use_case"].append(self._get_usecase())
        self.output["soc"].append(self.soc)
        self.output["charging_demand"].append(self._get_last_charging_demand())
        self.output["charging_power"].append(charging_power)
        self.output["consumption"].append(self._get_last_consumption())

    def charge(self, timestamp, start, time, power, new_soc):
        # TODO call spiceev charging depending on soc, location, task
        # TODO this requires a SpiceEV scenario object
        if not all(isinstance(i, int) or isinstance(i, float) for i in [start, time, power, new_soc]):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time, power, new_soc]):
            raise ValueError("Arguments can't be negative.")
        if new_soc < self.soc:
            raise ValueError("SoC of vehicle can't be lower after charging.")
        if new_soc - self.soc > time * power / 60 / self.vehicle_type.battery_capacity:
            raise ValueError("SoC can't be reached in specified time window with given power.")
        self.status = 'charging'
        self.soc = new_soc
        self._update_activity(timestamp, start, time, charging_power=power)

    def drive(self, timestamp, start, time, destination, new_soc):
        # call drive api with task, soc, ...
        if not all(isinstance(i, int) or isinstance(i, float) for i in [start, time, new_soc]):
            raise TypeError("Argument has wrong type.")
        if not isinstance(destination, str):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time, new_soc]):
            raise ValueError("Arguments can't be negative.")
        if new_soc > self.soc:
            raise ValueError("SoC of vehicle can't be higher after driving.")
        if (self.soc - new_soc >
                self.vehicle_type.base_consumption * time / 60 * 100 / self.vehicle_type.battery_capacity):
            raise ValueError("Consumption too high.")
        self.status = 'driving'
        self.soc = new_soc
        self._update_activity(timestamp, start, time)
        self.status = destination

    def park(self, timestamp, start, time):
        if not all(isinstance(i, int) or isinstance(i, float) for i in [start, time]):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time]):
            raise ValueError("Arguments can't be negative.")
        self.status = "parking"
        self._update_activity(timestamp, start, time)

    @property
    def usable_soc(self):
        return self.soc - self.vehicle_type.soc_min

    @property
    def scenario_info(self):
        scenario_dict = {
            "constants": {
                "vehicle_types": {
                    self.vehicle_type.name: {
                        "name": self.vehicle_type.name,
                        "capacity": self.vehicle_type.battery_capacity,
                        "mileage": self.vehicle_type.base_consumption * 100,
                        "charging_curve": self.vehicle_type.charging_curve,
                        "min_charging_power": self.vehicle_type.min_charging_power,
                        "v2g": False,
                        "v2g_power_factor": 0.5
                    }
                },
                "vehicles": {
                    f"{self.vehicle_type.name}_0": {
                        # "connected_charging_station": self.current_location.location_id,
                        "desired_soc": 1,
                        "soc": self.soc,
                        "vehicle_type": self.vehicle_type.name
                    }
                }
            }
        }
        return scenario_dict

    def _get_last_charging_demand(self):
        if len(self.output["soc"]) > 1:
            charging_demand = (self.output["soc"][-1] - self.output["soc"][-2])
            charging_demand *= self.vehicle_type.battery_capacity
            return max(round(charging_demand, 4), 0)
        else:
            return 0

    def _get_last_consumption(self):
        if len(self.output["soc"]) > 1:
            last_consumption = self.output["soc"][-1] - self.output["soc"][-2]
            last_consumption *= self.vehicle_type.battery_capacity
            return abs(min(round(last_consumption, 4), 0))
        else:
            return 0