from dataclasses import dataclass, field
from typing import Optional, List, Dict
import pandas as pd
import pathlib
from fleema.location import Location
from fleema.event import Status, Task


@dataclass
class VehicleType:
    """The VehicleType contains static vehicle data.

    Parameters
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
    battery_capacity: float = 50.0
    soc_min: float = 0.2
    base_consumption: float = (
        0.0  # TODO decide if this is necessary, currently used for spiceev?
    )
    charging_capacity: dict = field(default_factory=dict)
    charging_curve: list = field(default_factory=list)
    min_charging_power: float = 0.0
    event_csv: bool = True
    label: Optional[str] = None
    v2g: bool = False
    v2g_power_factor: float = 0.5

    @property
    def plugs(self):
        return list(self.charging_capacity.keys())


class Vehicle:
    """The vehicle contains tech parameters as well as tasks.

    Parameters
    ----------
    id : str
        ID of the vehicle.
    vehicle_type : VehicleType
        VehicleType of the Vehicle instance.
    status : Status
        Describes current state of the Vehicle object wrapped in an Enum.
        Status: DRIVING, PARKING, CHARGING
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

    def __init__(
        self,
        vehicle_id: str,
        vehicle_type: "VehicleType" = VehicleType(),
        status: Status = Status.PARKING,
        soc: float = 1.0,
        rotation: Optional[str] = None,
        current_location: Optional["Location"] = None,
    ):
        """Constructor of the Vehicle class.

        Parameters
        ----------
        id : str
            ID of the vehicle.
        vehicle_type : VehicleType
            VehicleType of the Vehicle instance. Default instantiates a VehicleType object.
        status : Status
            Describes current state of the Vehicle object wrapped in an Enum.
            Status: DRIVING, PARKING, CHARGING
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
        self.soc_start = soc
        self.soc = soc
        self.rotation = rotation
        self.current_location = current_location
        self.tasks: Dict[int, "Task"] = {}
        self.schedule = (
            None  # TODO add dataframe which has information for all timesteps
        )

        self.output: dict = {
            "timestamp": [],
            "event_start": [],
            "event_time": [],
            "end_location": [],
            "status": [],
            "soc_start": [],
            "soc_end": [],
            "energy": [],
            "actual_energy_from_grid": [],
            "station_charging_capacity": [],
            "average_charging_power": [],
            "distance": [],
            "energy_from_feed_in": [],
            "energy_from_grid": [],
            "energy_cost": [],
            "emission": [],
            "consumption": [],
            "level_of_loading": [],
            "v2g_energy": [],
        }

    def _update_activity(
        self,
        timestamp,
        event_start,
        event_time,
        simulation_state,
        charging_power=0.0,
        nominal_charging_capacity=0.0,
        distance=0.0,
        charging_result=None,
        interp_consumption=0.0,
        level_of_loading=0.0,
    ):
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
        nominal_charging_capacity : float
            Power of the connected charging point.
        distance : float
            Potential distance between two locations. Default is zero.
        charging_result : charging_result : dict[string, float]
            Default is None.
        interp_consumption : float
            Consumption from when driving, calculated by the driving simulation. Default is zero.
        level_of_loading : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle.

        """
        if self.vehicle_type.event_csv:
            self.soc = self.soc
            self.output["timestamp"].append(timestamp)
            self.output["event_start"].append(event_start)
            self.output["event_time"].append(event_time)
            self.output["status"].append(self.status)
            self.output["soc_start"].append(
                self.output["soc_end"][-1]
                if len(self.output["soc_end"]) > 0
                else self.soc_start
            )
            self.output["soc_end"].append(self.soc)
            charging_demand = self._get_last_charging_demand()
            consumption = self._get_last_consumption()
            self.output["energy"].append(charging_demand + consumption)
            self.output["station_charging_capacity"].append(nominal_charging_capacity)
            self.output["average_charging_power"].append(charging_power)
            self.output["distance"].append(distance)
            self.output["level_of_loading"].append(level_of_loading)
            if charging_result is not None:
                self.output["actual_energy_from_grid"].append(
                    charging_result["grid_energy"]
                )
                energy_from_feed_in = charging_demand * charging_result["feed_in"]
                self.output["energy_from_feed_in"].append(energy_from_feed_in)
                self.output["energy_from_grid"].append(
                    charging_demand - energy_from_feed_in
                )
                self.output["energy_cost"].append(charging_result["cost"])
                self.output["emission"].append(charging_result["emission"])
                self.output["v2g_energy"].append(charging_result["v2g_energy"])
            else:
                self.output["actual_energy_from_grid"].append(0)
                self.output["energy_from_feed_in"].append(0)
                self.output["energy_from_grid"].append(0)
                self.output["energy_cost"].append(0)
                self.output["emission"].append(0)
                self.output["v2g_energy"].append(0)

            if self.current_location is not None:
                self.output["end_location"].append(self.current_location.name)
            else:
                self.output["end_location"].append("")
            if simulation_state is not None:
                simulation_state.update_vehicle(self)
                simulation_state.log_data(
                    charging_demand, charging_result, distance, consumption
                )
            self.output["consumption"].append(interp_consumption)

    def add_task(self, task: "Task"):
        """Add a task to the self.tasks using the start_time as key."""
        if task.start_time in self.tasks:
            raise KeyError(
                f"Key {task.start_time} already exists in tasks of vehicle {self.id}"
            )
        # otherwise, add new task to list, ordered by starting time
        self.tasks[task.start_time] = task

    def remove_task(self, task: Optional["Task"]):
        """Remove a task from self.tasks."""
        if task is None:
            return
        if self.tasks[task.start_time] == task:
            del self.tasks[task.start_time]
        else:
            raise ValueError(
                f"Task {task.__str__} is not in task list of vehicle {self.id} or has the wrong index"
            )

    def get_task(self, time_step: int):
        try:
            return self.tasks[time_step]
        except KeyError:
            return None

    def get_next_task(self, time_step: int):
        "Returns next task, not including the given timestep."
        # get the biggest tasks key (last time step where a task starts)
        last_task_start = max(self.tasks)
        # only runs, if a task comes after specified time step
        if time_step <= last_task_start:
            # check every timestep for a new task, until one is found
            for i in range(time_step + 1, last_task_start + 1):
                task = self.get_task(i)
                if task is not None:
                    return task
        else:
            return None

    @property
    def has_valid_task_list(self):
        previous_task = None
        for timestep, task in sorted(self.tasks.items()):
            if previous_task is not None:
                if not (
                    previous_task.end_point == task.start_point
                    and previous_task.end_time <= task.start_time
                ):
                    print(f"Warning: Error found in task list at timestep {timestep}.")
                    return False
            previous_task = task
        return True

    def get_breaks(self, start: int, end: int) -> List["Task"]:
        """Get break times according to self.tasks

        Parameters
        ----------
        start : int
            Starting timestep
        end : int
            Ending timestep
        """
        if not self.has_valid_task_list:
            print(f"Task list of vehicle {self.id} is not valid.")
            # Error disabled for testing purposes until schedule is fixed
            # raise AttributeError(f"Task list of vehicle {self.id} is not valid.")
        breaks = []
        _, first_task = sorted(self.tasks.items())[0]
        if first_task.start_time > start:
            breaks.append(
                Task(
                    start,
                    first_task.start_time,
                    first_task.start_point,
                    first_task.start_point,
                    Status.BREAK,
                )
            )
        previous_task = first_task
        for _, task in sorted(self.tasks.items()):
            if task.end_time < end and task.task == Status.DRIVING:
                # TODO are other task types relevant?
                if task.start_time > previous_task.end_time:
                    breaks.append(
                        Task(
                            previous_task.end_time,  # TODO maybe +1?
                            task.start_time,  # TODO maybe -1?
                            previous_task.end_point,
                            task.start_point,
                            Status.BREAK,
                        )
                    )
                previous_task = task
        if previous_task.end_time < end:
            breaks.append(
                Task(
                    previous_task.end_time,  # TODO maybe +1?
                    end,  # TODO maybe -1?
                    previous_task.end_point,
                    previous_task.end_point,
                    Status.BREAK,
                )
            )
        return breaks

    def charge(
        self,
        timestamp,
        start,
        time,
        power,
        new_soc,
        charging_capacity,
        level_of_loading=0.0,
        charging_result=None,
        observer=None,
    ):
        """This method updates the vehicle with charging results.

        Parameters
        ----------
        timestamp : str
        start : int
        time : int
        power : float
        new_soc : float
        charging_capacity : float
        level_of_loading : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle.
        charging_result : dict[string, float]
        observer : Optional[SimulationState]
        """
        if not all(
            isinstance(i, int) or isinstance(i, float)
            for i in [start, time, power, new_soc]
        ):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time, power, new_soc]):
            raise ValueError("Arguments can't be negative.")
        if new_soc < self.soc:
            raise ValueError("SoC of vehicle can't be lower after charging.")
        if new_soc - self.soc > time * power / 60 / self.vehicle_type.battery_capacity:
            raise ValueError(
                "SoC can't be reached in specified time window with given power."
            )
        self.status = Status.CHARGING
        self.soc = new_soc
        self._update_activity(
            timestamp,
            start,
            time,
            observer,
            charging_power=power,
            nominal_charging_capacity=charging_capacity,
            charging_result=charging_result,
            level_of_loading=level_of_loading,
        )

    def drive(
        self,
        timestamp,
        start: int,
        time: int,
        destination: "Location",
        new_soc: float,
        distance: float,
        level_of_loading=0.0,
        observer=None,
        interp_consumption=0.0,
    ):
        """This method updates the vehicle with driving results.

        Parameters
        ----------
        timestamp : str
        start : int
        time : int
        destination : Location
        new_soc : float
        distance : float
        level_of_loading : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle.
        observer : Optional[SimulationState]
        interp_consumption : float

        """
        # call drive api with task, soc, ...
        if not all(
            isinstance(i, int) or isinstance(i, float) for i in [start, time, new_soc]
        ):
            raise TypeError("Argument has wrong type.")
        if not isinstance(destination, Location):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time]):
            raise ValueError("Arguments can't be negative.")
        if new_soc <= 0:
            raise ValueError(
                f"SoC of vehicle {self.id} became negative at {timestamp}!"
            )
        if new_soc > self.soc:
            raise ValueError("SoC of vehicle can't be higher after driving.")
        # if (
        #     self.soc - new_soc
        #     > self.vehicle_type.base_consumption
        #     * time
        #     / 60
        #     * 100
        #     / self.vehicle_type.battery_capacity
        # ):
        #     raise ValueError("Consumption too high.")
        # if new_soc < self.soc_min:
        #     raise ValueError(
        #         f"SoC of vehicle {self.id} became smaller than the minimum SoC at {timestamp}."
        #     )
        self.status = Status.DRIVING
        self.soc = new_soc
        self.current_location = destination
        self._update_activity(
            timestamp,
            start,
            time,
            observer,
            distance=distance,
            interp_consumption=interp_consumption,
            level_of_loading=level_of_loading,
        )

    def park(self, timestamp, start, time, observer=None):
        """This method updates the vehicle after a parking event."""
        if not all(isinstance(i, int) or isinstance(i, float) for i in [start, time]):
            raise TypeError("Argument has wrong type.")
        if not all(i >= 0 for i in [start, time]):
            raise ValueError("Arguments can't be negative.")
        self.status = Status.PARKING
        self._update_activity(timestamp, start, time, observer)

    def export(self, directory):
        """
        Exports the output values collected in vehicle object to a csv file.

        Parameters
        ----------
        directory : :obj:`pathlib.Path`
            Save directory

        """
        if self.vehicle_type.event_csv:
            activity = pd.DataFrame(self.output)

            activity = activity.reset_index(drop=True)
            activity = activity.round(4)
            activity.to_csv(pathlib.Path(directory, f"{self.id}_events.csv"))

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
            "components": {
                "vehicle_types": {
                    self.vehicle_type.name: {
                        "name": self.vehicle_type.name,
                        "capacity": self.vehicle_type.battery_capacity,
                        "mileage": self.vehicle_type.base_consumption * 100,
                        "charging_curve": self.vehicle_type.charging_curve,
                        "min_charging_power": self.vehicle_type.min_charging_power,
                        "v2g": self.vehicle_type.v2g,
                        "v2g_power_factor": self.vehicle_type.v2g_power_factor,
                    }
                },
                "vehicles": {
                    self.id: {
                        # "connected_charging_station": self.current_location.location_id,
                        "desired_soc": 1,
                        "soc": self.soc,
                        "vehicle_type": self.vehicle_type.name,
                    }
                },
            }
        }
        return scenario_dict

    def _get_last_charging_demand(self):
        """Returns the charging demand of the previous event."""
        if len(self.output["soc_start"]):
            charging_demand = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            charging_demand *= self.vehicle_type.battery_capacity
            return max(charging_demand, 0)
        else:
            return 0

    def _get_last_consumption(self):
        """Returns the consumption of the last event."""
        if len(self.output["soc_start"]):
            last_consumption = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            last_consumption *= self.vehicle_type.battery_capacity
            return min(last_consumption, 0)
        else:
            return 0
