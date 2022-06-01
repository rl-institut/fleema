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

    def _update_activity(self, timestamp, event_start, event_time,
                         nominal_charging_capacity=0, charging_power=0):
        """Records newest energy and activity"""
        self.soc = round(self.soc, 4)
        self.output["timestamp"].append(timestamp)
        self.output["event_start"].append(event_start)
        self.output["event_time"].append(event_time)
        self.output["location"].append(self.status)
        # self.output["use_case"].append(self._get_usecase())
        self.output["soc"].append(self.soc)
        self.output["charging_demand"].append(self._get_last_charging_demand())
        self.output["nominal_charging_capacity"].append(nominal_charging_capacity)
        self.output["charging_power"].append(charging_power)
        self.output["consumption"].append(self._get_last_consumption())

    def charge(self, trip, power, charging_type):
        # call spiceev charging depending on soc, location, task
        self.status = 'charging'
        usable_power = min(power, self.vehicle_type.charging_capacity[charging_type])
        self.soc = min(self.soc + trip.park_time * usable_power / self.vehicle_type.battery_capacity, 1)
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                              nominal_charging_capacity=power, charging_power=usable_power)
        return

    def drive(self, trip):
        # call drive api with task, soc, ...
        self.status = 'driving'
        self.soc -= self.vehicle_type.base_consumption * trip.distance / self.vehicle_type.battery_capacity
        self._update_activity(trip.drive_timestamp, trip.drive_start, trip.drive_time)
        self.status = trip.destination

        return

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
    battery_capacity: float
    base_consumption: float
    charging_capacity: dict
    charging_curve: list
    min_charging_power: float


# example inherited class as proof of concept, remove later if unused
@dataclass
class BusType(VehicleType):
    max_passenger_number: int
