"""This script includes the Simulation class.

Classes
-------
Simulation
"""

import configparser as cp
import pathlib
import pandas as pd
import json
import datetime
import warnings
from typing import List, Dict, Union

from advantage.location import Location
from advantage.vehicle import Vehicle, VehicleType
from advantage.event import Task
from advantage.charger import Charger, PlugType
from advantage.simulation_state import SimulationState
from advantage.simulation_type import class_from_str
from advantage.ride import RideCalc
from advantage.spiceev_interface import get_spice_ev_scenario_dict, run_spice_ev
from advantage.event import Status

from advantage.util.conversions import (
    date_string_to_datetime,
    datetime_string_to_datetime,
    step_to_timestamp,
)


class Simulation:
    """This class can import a specified config directory and build a Simulation out of the given scenario.

    It also contains the run function, which starts the simulation.

    Parameters
    ----------
    soc_min : float
        Lower limit of the battery's charging power (soc - state of charge).
    rng_seed : int
        Seed for generating numbers pseudo-randomly.
    min_charging_power: float
        Minimum charging power of the vehicles.
    start_date : datetime.date
        Start date of the simulation.
    end_date : datetime.date
        End date of the simulation.
    num_threads : int
        Number of threads to determine the concurrency of the simulation.
    schedule : pandas.core.frame.DataFrame
        Pandas Dataframe with information about the specific route of the given vehicle fleet.
    vehicle_types : dict
        Dictionary with strings of types of vehicles as keys and instances of the class VehicleType as values.
    locations : dict
        Dictionary with strings of locations as keys and instances of the class Location as the values.
    plug_types : dict
        Dictionary with strings of the plug-type and dictionaries comprised of the name, capacity and charging_type
        as values.
    weights : dict
        Dictionary with weight factors for all criteria of the charging point evaluation function.

    """

    def __init__(
        self,
        schedule: pd.DataFrame,
        vehicle_types,
        charging_points,
        cfg_dict,
        consumption_dict,
    ):
        """Init Method of the Simulation class.

        Parameters
        ----------
        schedule : pandas.core.frame.DataFrame
            Pandas Dataframe with information about the specific route of the given vehicle fleet.
        vehicle_types : dict
            Dictionary with the given types of vehicles and their features that are used in the scenario.
        charging_points : dict
            Dictionary with the given types of charging points and their features that are used in the scenario.
        cfg_dict : dict
            Dictionary with configuration details which are used in the Simulation class to influence the outcome.

        """
        self.soc_min = cfg_dict["soc_min"]
        # TODO check if it's enough to have min_charging_power in vehicle, else add to charger
        self.rng_seed = cfg_dict["rng_seed"]
        self.min_charging_power = cfg_dict["min_charging_power"]
        self.start_date = cfg_dict["start_date"]
        self.end_date = cfg_dict["end_date"]
        self.step_size = cfg_dict["step_size"]
        time_steps: datetime.timedelta = self.end_date - self.start_date
        self.time_steps = int(time_steps.total_seconds() / 60 / self.step_size)
        self.time_series = pd.date_range(
            self.start_date,
            self.end_date,
            freq=f"{self.step_size}min",
            inclusive="left",
        )
        self.end_of_day_steps = None
        self.num_threads = cfg_dict["num_threads"]
        self.simulation_type = (
            "schedule"  # TODO implement in config (schedule vs ondemand)
        )
        self.weights = cfg_dict["weights"]
        self.outputs = cfg_dict["outputs"]

        # TODO use scenario name in save_directory once scenario files have been reorganized
        save_directory_name = "{}_{}".format(
            self.simulation_type, datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        )
        self.save_directory = pathlib.Path("results", save_directory_name)

        self.schedule = schedule

        # driving simulation
        consumption = consumption_dict["consumption"]
        distances = consumption_dict["distance"]
        inclines = consumption_dict["incline"]

        self.driving_sim = RideCalc(consumption, distances, inclines)

        # use other args to create objects
        self.vehicle_types: Dict[str, "VehicleType"] = {}
        for name, info in vehicle_types.items():
            self.vehicle_types[name] = VehicleType(
                name,
                info["capacity"],
                self.soc_min,
                0,
                info["charging_power"],
                info["charging_curve"],
                self.min_charging_power,
                self.outputs["vehicle_csv"],
            )
        self.vehicles: Dict[Union[str, int], "Vehicle"] = {}

        self.locations: Dict[str, "Location"] = {}
        for location_name in self.schedule.departure_name.unique():
            self.locations[location_name] = Location(location_name)

        self.plug_types: Dict[int, "PlugType"] = {}
        self.charging_locations: List["Location"] = []
        for name, info in charging_points["plug_types"].items():
            self.plug_types[name] = PlugType(name, info["capacity"], info["plug"])
        for name, info in charging_points["charging_points"].items():
            plug_types = [
                p for p in self.plug_types.values() if p.name in info["plug_types"]
            ]
            charger = Charger.from_json(
                name, info["number_charging_points"], plug_types
            )
            self.locations[name].chargers.append(charger)
            if "grid_connection" in info:
                self.locations[name].set_power(float(info["grid_connection"]))
            else:
                self.locations[name].set_power(50.0)
            # TODO add grid info to location here?
            if not self.locations[name] in self.charging_locations:
                self.charging_locations.append(self.locations[name])

        # Instantiation of observer
        self.observer = SimulationState()

    def get_end_of_day_timestep(self, step):
        """Returns the last time step of the day of the given step.

        Parameters
        ----------
        step : int
            Reference time step.

        Returns
        -------
        int
            End of day time step
        """
        if self.end_of_day_steps is None:
            steps_per_day = 1440 / self.step_size
            days = int(self.time_steps / steps_per_day)
            self.end_of_day_steps = [d * steps_per_day for d in range(days)]
        for i in self.end_of_day_steps:
            if step < i:
                return step
        raise ValueError(
            f"Step {step} higher than end of day time steps: {self.end_of_day_steps}"
        )

    def vehicles_from_schedule(self):
        """Creates vehicle objects from the schedule."""
        vehicle_ids = self.schedule.groupby(by="vehicle_id")
        for vehicle_id, index in vehicle_ids.groups.items():
            vehicle_type = self.schedule.loc[index, "vehicle_type"].unique()  # type: ignore
            if len(vehicle_type) != 1:
                raise ValueError(
                    f"Vehicle number {vehicle_id} has multiple vehicle types assigned to it!"
                )
            self.vehicles[vehicle_id] = Vehicle(
                vehicle_id, self.vehicle_types[vehicle_type[0]], soc_min=self.soc_min
            )

    def task_from_schedule(self, row):  # TODO move function to vehicle?
        """Creates Task from a specificed schedule row and adds it to the vehicle.

        Parameters
        ----------
        row : pd.Series
            Row of schedule DataFrame

        """
        vehicle = self.vehicles[row.vehicle_id]
        trip = self.driving_sim.calculate_trip(
            self.locations[row.departure_name],
            self.locations[row.arrival_name],
            vehicle.vehicle_type,
        )
        dep_time = self.datetime_to_timesteps(row.departure_time)
        arr_time = self.datetime_to_timesteps(row.arrival_time)
        calc_time = dep_time + int(round(trip["trip_time"], 0))
        if calc_time > arr_time:
            warnings.warn(
                f"""Calculated time for trip {row.departure_name} to {row.arrival_name} is higher than in schedule.
                (Calculated: {calc_time - dep_time}, schedule: {arr_time - dep_time})\n"""
            )
        task = Task(
            dep_time,
            arr_time,  # TODO maybe use calc_time here in future, currently leads to errors
            self.locations[row.departure_name],
            self.locations[row.arrival_name],
            Status.DRIVING,
            trip["trip_time"],
            trip["soc_delta"],
        )
        vehicle.add_task(task)

    def run(self):
        """Creates SimulationType object depending on self.simulation_type and runs it."""
        sim = class_from_str(self.simulation_type)(self)
        sim.run()

    def datetime_to_timesteps(self, datetime_str):  # TODO move to conversions
        """Converts a given datetime string into a time step.

        Parameters
        ----------
        datetime_str : str
            Datetime string of the format YYYY-mm-dd HH:MM:SS

        Returns
        -------
        int
            Corresponding time step

        """
        delta = datetime_string_to_datetime(datetime_str) - self.start_date
        diff_in_minutes = delta.total_seconds() / 60
        return int(diff_in_minutes / self.step_size)

    def call_spiceev(
        self,
        location: "Location",
        start_time: int,
        end_time: int,
        vehicle: "Vehicle",
        point_id=None,
    ):
        """Calls SpiceEV with given parameters.

        Parameters
        ----------
        location : Location
        start_time : int
        end_time : int
        vehicle : Vehicle
        point_id : Optional[str]

        Returns
        -------
        Scenario
            SpiceEV scenario object

        """
        time_stamp = step_to_timestamp(self.time_series, start_time)
        charging_time = int(end_time - start_time)
        spice_dict = get_spice_ev_scenario_dict(
            vehicle, location, point_id, time_stamp, charging_time
        )
        spice_dict["constants"]["vehicles"][vehicle.id][
            "connected_charging_station"
        ] = list(spice_dict["constants"]["charging_stations"].keys())[0]
        scenario = run_spice_ev(spice_dict, "balanced")
        return scenario

    def evaluate_charging_location(
        self,
        vehicle_type: "VehicleType",
        charging_location: "Location",
        current_location: "Location",
        next_location: "Location",
        start_time: int,
        end_time: int,
        current_soc: float,
    ):
        """Gives a grade to a charging location.

        Parameters
        ----------
        vehicle_type : VehicleType
            Vehicle type of the vehicle that wants to charge
        charging_location : Location
            Location of the charger
        current_location : Location
            Location of the vehicle
        next_location : Location
            Starting location of the vehicles next task
        start_time : int
            Starting time step of the time window
        end_time : int
            Ending time step of the time window
        current_soc : float
            SoC of vehicle before charging

        Returns
        -------
        dict[float, float, float, float, Task, Optional[Task], Optional[Task]]
            Keys: "score", "consumption" (soc delta), "charge" (soc delta), "delta_soc" (total soc delta),
            "charge_event", Optional: "task_to", "task_from"

        """
        # return value in case of failure
        empty_dict = {"score": 0, "consumption": 0, "charge": 0, "delta_soc": 0}
        # run pre calculations
        time_window = end_time - start_time
        trip_to = self.driving_sim.calculate_trip(
            current_location, charging_location, vehicle_type
        )
        trip_from = self.driving_sim.calculate_trip(
            charging_location, next_location, vehicle_type
        )
        driving_time = int(trip_to["trip_time"] + trip_from["trip_time"])
        drive_soc = trip_to["soc_delta"] + trip_from["soc_delta"]
        # score the time spent charging and driving
        time_score = 1 - (driving_time / time_window)
        if time_score <= 0:
            return empty_dict
        # call spiceev to calculate charging
        charging_start = int(start_time + round(trip_to["trip_time"], 0))
        charging_time = time_window - driving_time
        mock_vehicle = Vehicle("vehicle", vehicle_type, soc=current_soc)
        spiceev_scenario = self.call_spiceev(
            charging_location,
            charging_start,
            charging_start + charging_time,
            mock_vehicle,
        )
        charged_soc = spiceev_scenario.socs[-1][0] - current_soc  # type: ignore
        if charged_soc <= 0:
            return empty_dict
        charge_score = 1 - ((-drive_soc) / charged_soc)
        if charge_score <= 0:
            return empty_dict

        # calculate remaining scores which don't have cutoff criteria
        cost_score = 0  # TODO get €/kWh from inputs
        local_ee_score = 0  # TODO energy_from_ee / charged_energy
        soc_score = 0.1 if current_soc < 0.8 else 0
        score = (
            time_score * self.weights["time_factor"]
            + charge_score * self.weights["energy_factor"]
            + cost_score * self.weights["cost_factor"]
            + local_ee_score * self.weights["local_renewables_factor"]
            + soc_score  # TODO discuss with team
        )
        if score <= 0:
            return empty_dict

        charge_event = Task(
            charging_start,
            charging_start + charging_time,
            charging_location,
            charging_location,
            Status.CHARGING,
        )
        result_dict = {
            "score": score,
            "consumption": drive_soc,
            "charge": charged_soc,
            "delta_soc": charged_soc + drive_soc,
            "charge_event": charge_event,
        }
        # create drive to and drive from charging point
        if current_location is not charging_location:
            task_to = Task(
                start_time,
                charging_start,
                current_location,
                charging_location,
                Status.DRIVING,
                trip_to["trip_time"],
                trip_to["soc_delta"],
            )
            result_dict["task_to"] = task_to
        if charging_location is not next_location:
            task_from = Task(
                charging_start + charging_time,
                end_time,
                charging_location,
                next_location,
                Status.DRIVING,
                trip_to["trip_time"],
                trip_to["soc_delta"],
            )
            result_dict["task_from"] = task_from
        return result_dict

    @classmethod
    def from_config(cls, scenario_name, no_outputs_mode=False):
        """Creates a Simulation object from the specified scenario.

        The scenario needs to be located in the directory /scenarios.
        A scenario consists of different inputs like charging_points, schedule, vehicle_types
        and a config file called scenario which are read and processed in order to create a Simulation object.

        Parameters
        ----------
        scenario_name : str
            Name of the scenario and the directory in which the necessary input lies.

        Returns
        -------
        Simulation
            Simulation object

        Raises
        ------
        FileNotFoundError
            If the scenario is not found in the ./scenarios directory.
            If the config file scenario.cfg is not found or can't be read..

        """
        scenario_path = pathlib.Path("scenarios", scenario_name)
        if not scenario_path.is_dir():
            raise FileNotFoundError(
                f"Scenario {scenario_name} not found in ./scenarios."
            )

        # read config file
        cfg = cp.ConfigParser()
        cfg_file = pathlib.Path(scenario_path, "scenario.cfg")
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Config file {cfg_file} not found.")
        try:
            cfg.read(cfg_file)
        except Exception:
            raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

        schedule = pd.read_csv(
            pathlib.Path(scenario_path, cfg["files"]["schedule"]), sep=","
        )

        vehicle_types_file = cfg["files"]["vehicle_types"]
        ext = vehicle_types_file.split(".")[-1]
        if ext != "json":
            print("File extension mismatch: vehicle type file should be .json")
        with open(pathlib.Path(scenario_path, cfg["files"]["vehicle_types"])) as f:
            vehicle_types = json.load(f)
        vehicle_types = vehicle_types["vehicle_types"]

        charging_points_file = cfg["files"]["charging_points"]
        ext = charging_points_file.split(".")[-1]
        if ext != "json":
            print("File extension mismatch: charging_point file should be .json")
        with open(pathlib.Path(scenario_path, cfg["files"]["charging_points"])) as f:
            charging_points = json.load(f)

        start_date = cfg.get("basic", "start_date")
        start_date = date_string_to_datetime(start_date)
        end_date = cfg.get("basic", "end_date")
        end_date = date_string_to_datetime(end_date) + datetime.timedelta(1)

        # parse output options
        vehicle_csv = cfg.getboolean("outputs", "vehicle_csv")

        outputs = {
            "vehicle_csv": vehicle_csv,
        }

        if no_outputs_mode:
            outputs = {key: False for key in outputs}

        # parse weights
        weights_dict = {
            "time_factor": cfg.getfloat("weights", "time_factor"),
            "energy_factor": cfg.getfloat("weights", "energy_factor"),
            "cost_factor": cfg.getfloat("weights", "cost_factor"),
            "local_renewables_factor": cfg.getfloat(
                "weights", "local_renewables_factor"
            ),
        }

        cfg_dict = {
            "soc_min": cfg.getfloat("charging", "soc_min"),
            "min_charging_power": cfg.getfloat("charging", "min_charging_power"),
            "rng_seed": cfg["sim_params"].getint("seed", None),
            "start_date": start_date,
            "end_date": end_date,
            "num_threads": cfg.getint("sim_params", "num_threads"),
            "step_size": cfg.getint("basic", "step_size"),
            "weights": weights_dict,
            "outputs": outputs,
        }

        # read consumption_table
        consumption_path = pathlib.Path(scenario_path, cfg["files"]["consumption"])
        consumption_df = pd.read_csv(consumption_path)

        # read distance table
        distance_table = pathlib.Path(scenario_path, cfg["files"]["distance"])
        distance_df = pd.read_csv(distance_table, index_col=0)

        # read incline table
        incline_table = pathlib.Path(scenario_path, cfg["files"]["incline"])
        incline_df = pd.read_csv(incline_table, index_col=0)

        consumption_dict = {
            "consumption": consumption_df,
            "distance": distance_df,
            "incline": incline_df,
        }

        return Simulation(
            schedule, vehicle_types, charging_points, cfg_dict, consumption_dict
        )
