from dataclasses import dataclass, field
from advantage.location import Location
from typing import Optional


@dataclass
class VehicleType:
    """The VehicleType contains static vehicle data.

    Attributes
    ----------
    name : str
        Vehicle type name.
    battery_capacity : float
        Battery capacity in kWh.
    soc_min : float
        Minimum state of charge that should remain in battery after a drive.
    base_consumption : float
        In kWh/km ?
    charging_capacity : dict
        Dictionary containing values for each viable plug and their respective power.
    charging_curve : list
        List of list with two numbers. First number is SoC (state of charge) and second the possible max power.
        Example: [[0, 50], [0.8, 50], [1, 20]].
    plugs : list
        List of plugs this vehicle can use. Example: ["Type2", "Schuko"].
    min_charging_power : float
        Least amount of charging power possible, as a share of max power.
    label : str, optional

    """
    name: str = "vehicle_name"
    battery_capacity: float = 50.
    soc_min: float = 0.
    base_consumption: float = 0.  # TODO decide if this is necessary
    charging_capacity: dict = field(default_factory=dict)
    charging_curve: list = field(default_factory=list)
    min_charging_power: float = 0.
    label: Optional[str] = None

    @property
    def plugs(self):
        return list(self.charging_capacity.keys())


# example inherited class as proof of concept, TODO remove later if unused
@dataclass
class BusType(VehicleType):
    """This class implements the basic bus type with the parent class VehicleType.

    Attributes
    ----------
    name : str
        Vehicle type name.

    """

    max_passenger_number: int = 0


class Vehicle:
    """The vehicle contains tech parameters as well as tasks.

    Attributes
    ----------
    vehicle_type : VehicleType
        VehicleType of the Vehicle instance.
    status : str
        Describes current state of the Vehicle object. Example: "parking", "driving", "charging"
    soc : float
        State of charge: Current charge of the battery.
    availability : bool
        Boolean that states if Vehicle is avaiable. Default on True.
    rotation : str, optional
    current_location : Location, optional
        Has current location if Vehicle was already to one assigned.
    task : None
    output: dict
        Comprises all relevant information of the Vehicle object like locations, statuses, etc.

    """

    def __init__(self,
                 vehicle_id: str,
                 vehicle_type: "VehicleType" = VehicleType(),
                 status: str = "parking",
                 soc: float = 1,
                 availability: bool = True,     # TODO Warum availability, wenn es schon einen Status gibt?
                 rotation: Optional[str] = None,
                 current_location: Optional["Location"] = None
                 ):
        self.id = vehicle_id
        self.vehicle_type = vehicle_type
        self.status = status
        self.soc = soc
        self.availability = availability
        self.rotation = rotation
        self.current_location = current_location
        self.task = None

        self.output: dict = {
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

    def _update_activity(self, timestamp, event_start, event_time, simulation_state, charging_power=0):
        """Records newest energy and activity in the attributes soc and output."""
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
        if simulation_state is not None:
            simulation_state.update_vehicle(self)

    def charge(self, timestamp, start, time, power, new_soc, observer=None):
        """This method simulates charging and updates therefore the attributes status and soc."""
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
        self._update_activity(timestamp, start, time, observer, charging_power=power)

    def drive(self, timestamp, start, time, destination, new_soc, observer=None):
        """This method simulates driving and updates therefore the attributes status and soc."""
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
        self._update_activity(timestamp, start, time, observer)
        self.status = destination

    def park(self, timestamp, start, time, observer=None):
        """This method simulates parking and updates therefore the attribute status."""
        if not all(isinstance(i, int) or isinstance(i, float) for i in [start, time]):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time]):
            raise ValueError("Arguments can't be negative.")
        self.status = "parking"
        self._update_activity(timestamp, start, time, observer)

    @property
    def usable_soc(self):
        return self.soc - self.vehicle_type.soc_min

    @property
    def scenario_info(self):
        """Returns Dictionary with general information about the Vehicle instance."""
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
