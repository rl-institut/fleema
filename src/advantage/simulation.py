import configparser as cp
import pathlib
import pandas as pd
import json

from advantage.util.conversions import date_string_to_datetime


class Simulation:
    """
    This class can import a specified config directory and build the scenarios.
    It also contains the run function, which starts the simulation.
    """

    def __init__(self):
        pass

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

        cfg_dict = {  # "step_size": cfg.getint("basic", "stepsize"),
                    "soc_min": cfg.getfloat("basic", "soc_min"),
                    # "charging_threshold": cfg.getfloat("basic", "charging_threshold"),
                    "rng_seed": cfg["sim_params"].getint("seed", None),
                    "start_date": start_date,
                    "end_date": end_date
                    }
        num_threads = cfg.getint('sim_params', 'num_threads')

        return Simulation()
