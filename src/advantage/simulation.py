import configparser as cp
import pathlib
import pandas as pd
import json

import advantage.vehicle as vehicle

from advantage.util.conversions import date_string_to_datetime


class Simulation:
    """
    This class can import a specified config directory and build the scenarios.
    It also contains the run function, which starts the simulation.
    """

    def __init__(self, schedule, vehicle_types, charging_points, cfg_dict):
        self.soc_min = cfg_dict["soc_min"]
        # TODO check if it's enough to have min_charging_power in vehicle, else add to charger
        self.rng_seed = cfg_dict["rng_seed"]
        self.min_charging_power = cfg_dict["min_charging_power"]
        self.start_date = cfg_dict["start_date"]
        self.end_date = cfg_dict["end_date"]
        self.num_threads = cfg_dict["num_threads"]

        self.schedule = schedule

        # use other args to create objects
        self.vehicle_types = {}
        for name, info in vehicle_types.items():
            self.vehicle_types[name] = vehicle.VehicleType(name, info["capacity"], self.soc_min, 0,
                                                           info["charging_power"], info["charging_curve"],
                                                           self.min_charging_power)

        for name, info in charging_points["charging_point_types"].items():
            pass
        for name, info in charging_points["charging_points"].items():
            pass

        self.run()

    def run(self):
        pass

    @classmethod
    def from_config(cls, scenario_name):
        """
        Creates a Simulation object from a specified scenario name. The scenario needs to be located in /scenarios.

        Returns:
            Simulation object
        """
        scenario_path = pathlib.Path("scenarios", scenario_name)
        if not scenario_path.is_dir():
            raise FileNotFoundError(f'Scenario "{scenario_path.stem}" not found in ./scenarios .')

        # read config file
        cfg = cp.ConfigParser()
        cfg_file = pathlib.Path(scenario_path, "scenario.cfg")
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Config file {cfg_file} not found.")
        try:
            cfg.read(cfg_file)
        except Exception:
            raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

        schedule = pd.read_csv(pathlib.Path(scenario_path, cfg["files"]["schedule"]), sep=',', index_col=0)

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
                    "num_threads": cfg.getint('sim_params', 'num_threads')
                    }

        return Simulation(schedule, vehicle_types, charging_points, cfg_dict)
