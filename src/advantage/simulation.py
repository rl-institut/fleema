import configparser as cp
import pathlib
import pandas as pd
import json
import datetime
from typing import List, Dict, Union

from advantage.location import Location
from advantage.vehicle import Vehicle, VehicleType, Task
from advantage.charger import Charger, PlugType
from advantage.simulation_state import SimulationState
from advantage.simulation_type import class_from_str

from advantage.util.conversions import date_string_to_datetime, datetime_string_to_datetime


class Simulation:
    """
    This class can import a specified config directory and build the scenarios.
    It also contains the run function, which starts the simulation.
    """

    def __init__(self, schedule: pd.DataFrame, vehicle_types, charging_points, cfg_dict):
        self.soc_min = cfg_dict["soc_min"]
        # TODO check if it's enough to have min_charging_power in vehicle, else add to charger
        self.rng_seed = cfg_dict["rng_seed"]
        self.min_charging_power = cfg_dict["min_charging_power"]
        self.start_date = cfg_dict["start_date"]
        self.end_date = cfg_dict["end_date"]
        self.step_size = cfg_dict["step_size"]
        time_steps: datetime.timedelta = self.end_date - self.start_date + datetime.timedelta(days=1)
        self.time_steps = int(time_steps.total_seconds() / 60 / self.step_size)
        self.end_of_day_steps = None
        self.num_threads = cfg_dict["num_threads"]
        self.simulation_type = "schedule"  # TODO implement in config (schedule vs ondemand)

        self.schedule = schedule
        self.events: List[tuple[int, "Vehicle"]] = []

        # use other args to create objects
        self.vehicle_types: Dict[str, "VehicleType"] = {}
        for name, info in vehicle_types.items():
            self.vehicle_types[name] = VehicleType(name, info["capacity"], self.soc_min, 0,
                                                   info["charging_power"], info["charging_curve"],
                                                   self.min_charging_power)
        self.vehicles: Dict[Union[str, int], "Vehicle"] = {}

        self.locations: Dict[str, "Location"] = {}
        for location_name in self.schedule.departure_name.unique():
            self.locations[location_name] = Location(location_name)

        self.plug_types: Dict[int, "PlugType"] = {}
        self.charging_locations: List["Location"] = []
        for name, info in charging_points["plug_types"].items():
            self.plug_types[name] = PlugType(name, info["capacity"], info["plug"])
        for name, info in charging_points["charging_points"].items():
            plug_types = [p for p in self.plug_types.values() if p.name in info["plug_types"]]
            charger = Charger.from_json(name, info["number_charging_points"], plug_types)
            self.locations[name].chargers.append(charger)
            if not self.locations[name] in self.charging_locations:
                self.charging_locations.append(self.locations[name])

        # Instantiation of observer
        self.observer = SimulationState()

    def get_end_of_day_timestep(self, step):
        if self.end_of_day_steps is None:
            steps_per_day = 1440 / self.step_size
            days = int(self.time_steps / steps_per_day)
            self.end_of_day_steps = [d * steps_per_day for d in range(days)]
        for i in self.end_of_day_steps:
            if step < i:
                return step
        raise ValueError(f"Step {step} higher than end of day time steps: {self.end_of_day_steps}")

    def vehicles_from_schedule(self):
        vehicle_ids = self.schedule.groupby(by="vehicle_id")
        for vehicle_id, index in vehicle_ids.groups.items():
            vehicle_type = self.schedule.loc[index, "vehicle_type"].unique()  # type: ignore
            if len(vehicle_type) != 1:
                raise ValueError(f"Vehicle number {vehicle_id} has multiple vehicle types assigned to it!")
            self.vehicles[vehicle_id] = Vehicle(vehicle_id, self.vehicle_types[vehicle_type[0]])  # type: ignore

    def task_from_schedule(self, row):  # TODO move function to vehicle?
        vehicle = self.vehicles[row.vehicle_id]
        task = Task(
            self.locations[row.departure_name],
            self.locations[row.arrival_name],
            self.datetime_to_timesteps(row.departure_time),
            self.datetime_to_timesteps(row.arrival_time),
            "driving"
        )
        vehicle.add_task(task)

    def run(self):
        sim = class_from_str(self.simulation_type)(self)
        sim.run()

    def datetime_to_timesteps(self, datetime_str):
        delta = datetime_string_to_datetime(datetime_str) - self.start_date
        diff_in_minutes = delta.total_seconds() / 60
        return diff_in_minutes / self.step_size

    def evaluate_charging_location(self, vehicle_type: "VehicleType", charging_location: "Location",
                                   current_location: "Location", next_location: "Location", time_window: int,
                                   current_soc: float, necessary_soc: float):
        # TODO get evaluation criteria from config
        # TODO calculate total time spent driving, extra distance and consumption
        driving_time = 0
        consumption = 0
        # TODO calculate possible charging amount and end_soc after extra drive
        charging_time = time_window - driving_time
        soc = current_soc - consumption / vehicle_type.battery_capacity
        # TODO evaluate charging point
        grade = 0
        return grade

    @classmethod
    def from_config(cls, scenario_name):
        """
        Creates a Simulation object from a specified scenario name. The scenario needs to be located in /scenarios.

        Returns:
            Simulation object
        """
        scenario_path = pathlib.Path("scenarios", scenario_name)
        if not scenario_path.is_dir():
            raise FileNotFoundError(f'Scenario {scenario_name} not found in ./scenarios.')

        # read config file
        cfg = cp.ConfigParser()
        cfg_file = pathlib.Path(scenario_path, "scenario.cfg")
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Config file {cfg_file} not found.")
        try:
            cfg.read(cfg_file)
        except Exception:
            raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

        schedule = pd.read_csv(pathlib.Path(scenario_path, cfg["files"]["schedule"]), sep=',')

        vehicle_types_file = cfg["files"]["vehicle_types"]
        ext = vehicle_types_file.split('.')[-1]
        if ext != "json":
            print("File extension mismatch: vehicle type file should be .json")
        with open(pathlib.Path(scenario_path, cfg["files"]["vehicle_types"])) as f:
            vehicle_types = json.load(f)
        vehicle_types = vehicle_types["vehicle_types"]

        charging_points_file = cfg["files"]["charging_points"]
        ext = charging_points_file.split('.')[-1]
        if ext != "json":
            print("File extension mismatch: charging_point file should be .json")
        with open(pathlib.Path(scenario_path, cfg["files"]["charging_points"])) as f:
            charging_points = json.load(f)

        start_date = cfg.get("basic", "start_date")
        start_date = date_string_to_datetime(start_date)
        end_date = cfg.get("basic", "end_date")
        end_date = date_string_to_datetime(end_date)

        cfg_dict = {
                    "soc_min": cfg.getfloat("charging", "soc_min"),
                    "min_charging_power": cfg.getfloat("charging", "min_charging_power"),
                    "rng_seed": cfg["sim_params"].getint("seed", None),
                    "start_date": start_date,
                    "end_date": end_date,
                    "num_threads": cfg.getint("sim_params", "num_threads"),
                    "step_size": cfg.getint("basic", "step_size")
                    }

        return Simulation(schedule, vehicle_types, charging_points, cfg_dict)
