import pandas as pd
from dataclasses import dataclass, field, asdict
from advantage.location import Location
from typing import Optional, List


@dataclass
class VehicleType:
    """The VehicleType contains static vehicle data.

    Attributes
    ----------
    name : str
        Name/ID for the vehicle type.
    battery_capacity : float
        Battery capacity in kWh.
    soc_min : float
        Minimum state of charge that should remain in battery after a drive. Shown in percentage.
    base_consumption : float
        Base/average consumption of the vehicle type in kWh/km.
    charging_capacity : dict
        Dictionary containing values for each viable plug and their respective capacity.
        Example: {"plug_0": 50, "plug_1": 150}
    charging_curve : list
        List of list with two numbers. First number is SoC (state of charge) and
        second the possible maximum power in kW. Example: [[0, 50], [0.8, 50], [1, 20]]
    min_charging_power : float
        Least amount of charging power possible, as a share of max power. Shown in percentage.
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


@dataclass
class Task:
    """
    Attributes
    ----------
    departure_point : Location
        Starting point of the task.
    arrival_point : Location
        End point of the task.
    departure_time : int
        Starting time of the task.
    arrival_time : int
        End time of the task.
    task : str
        Task type: driving, charging, parking, break.
    """
    departure_point: "Location"
    arrival_point: "Location"
    departure_time: int
    arrival_time: int
    task: str  # TODO enum

    @property
    def data_dict(self):
        return asdict(self)

    @property
    def dataframe(self):
        return pd.DataFrame.from_dict(self.data_dict)


class Vehicle:
    """The vehicle contains tech parameters as well as tasks.

    Attributes
    ----------
    id : str
        ID of the vehicle.
    vehicle_type : VehicleType
        VehicleType of the Vehicle instance.
    status : str
        Describes current state of the Vehicle object. Example: "parking", "driving", "charging"
    soc : float
        State of charge: Current charge of the battery. Shown in percentage.
    availability : bool
        Boolean that states if Vehicle is available. Default on True.
    rotation : str, optional
    current_location : Location, optional
        Has current location if Vehicle was already to one assigned.
    task : None
    output: dict
        Comprises all relevant information of the Vehicle object like locations, statuses, etc.
        It gets updated by the private method _update_activity.

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
        """Constructor of the Vehicle class.

        Parameters
        ----------
        id : str
            ID of the vehicle.
        vehicle_type : VehicleType
            VehicleType of the Vehicle instance. Default instantiates a VehicleType object.
        status : str
            Describes current state of the Vehicle object. Example: "parking", "driving", "charging"
        soc : float
            State of charge: Current charge of the battery. Shown in percentage.
        availability : bool
            Boolean that states if Vehicle is available. Default on True.
        rotation : str, optional
        current_location : Location, optional
            Current location of the Vehicle instance.

        """
        self.id = vehicle_id
        self.vehicle_type = vehicle_type
        self.status = status
        self.soc = soc
        self.availability = availability
        self.rotation = rotation
        self.current_location = current_location
        self.tasks: List["Task"] = []
        self.schedule = None    # TODO add dataframe which has information for all timesteps

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
        """Records newest energy and activity in the attributes soc and output.

        It is used when an event takes place. A event is one of the vehicle methods charge, drive or park.

        Parameters
        ----------
        timestamp : timestamp format --> YYYY-MM-DD hh:mm:ss, pandas._libs.tslibs.timestamps.Timestamp
            Timestamp that marks the time period of the event that is used.
        event_start : int
            Start of the event.
        event_time: int
            Time steps of the whole event.
        simulation_state : SimulationState
            Current state of the simulation.
        charging_power : float
            Charging power of the vehicle's battery in percentage. Default is zero.


        """
        self.soc = round(self.soc, 4)
        self.output["timestamp"].append(timestamp)
        self.output["event_start"].append(event_start)
        self.output["event_time"].append(event_time)
        self.output["location"].append(self.status)
        self.output["soc"].append(self.soc)
        self.output["charging_demand"].append(self._get_last_charging_demand())
        self.output["charging_power"].append(charging_power)
        self.output["consumption"].append(self._get_last_consumption())
        if simulation_state is not None:
            simulation_state.update_vehicle(self)

    def add_task(self, task: "Task"):
        # next upcoming tasks is a function of vehicle, taking a time step as input and giving the next task
        # observer stores upcoming task list?
        # if tasks empty, add new task to list
        if len(self.tasks) == 0:
            self.tasks.append(task)
        # otherwise, add new task to list, ordered by starting time
        else:
            task_added = False
            for count, it in enumerate(self.tasks):
                if task.departure_time < it.departure_time and not task_added:
                    self.tasks.insert(count, task)
                    task_added = True
            if not task_added:
                self.tasks.append(task)

    def remove_task(self, task: "Task"):
        if task in self.tasks:
            self.tasks.remove(task)

    def get_predicted_soc(self, start: int, end: int):
        consumption = 0
        for task in self.tasks:
            if start < task.arrival_time < end:
                if task.task == "driving":
                    # TODO run task through driving simulation, add result to consumption
                    pass
                if task.task == "charging":
                    # TODO check how much this would charge
                    pass
        return self.soc - consumption / self.vehicle_type.battery_capacity

    def get_breaks(self, start: int, end: int) -> List["Task"]:
        breaks = []
        first_task = self.tasks[0]
        if first_task.departure_time < start:
            breaks.append(Task(
                first_task.departure_point,
                first_task.departure_point,
                start,
                first_task.departure_time,
                "break")
            )
        previous_task = first_task
        for task in self.tasks:
            if task.arrival_time < end and task.task == "driving":  # TODO are other task types relevant?
                breaks.append(Task(
                    previous_task.arrival_point,
                    task.departure_point,
                    previous_task.arrival_time,  # TODO maybe +1?
                    task.departure_time,  # TODO maybe -1?
                    "break")
                )
                previous_task = task
        return breaks

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
        """This get method returns the SoC that is still usable until the vehicle reaches the minimum SoC.

        Returns
        -------
        float
            Usable SoC in percentage until the minimum SoC is reached.

        """
        return self.soc - self.vehicle_type.soc_min

    @property
    def scenario_info(self):
        """Returns Dictionary with general information about the Vehicle instance.

        Returns
        -------
            dict
                Nested dictionary with general information about the Vehicle instance.

        """
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
        """This private method is used by the method _update_activity and updates the charging demand."""
        if len(self.output["soc"]) > 1:
            charging_demand = (self.output["soc"][-1] - self.output["soc"][-2])
            charging_demand *= self.vehicle_type.battery_capacity
            return max(round(charging_demand, 4), 0)
        else:
            return 0

    def _get_last_consumption(self):
        """This private method is used by the method _update_activity and updates the last consumption."""
        if len(self.output["soc"]) > 1:
            last_consumption = self.output["soc"][-1] - self.output["soc"][-2]
            last_consumption *= self.vehicle_type.battery_capacity
            return abs(min(round(last_consumption, 4), 0))
        else:
            return 0
