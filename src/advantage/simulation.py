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

        start_date = cfg.get("basic", "start_date")
        start_date = date_string_to_datetime(start_date)
        end_date = cfg.get("basic", "end_date")
        end_date = date_string_to_datetime(end_date)

        # TODO get options from config
        # car_output = cfg.getboolean("output", "vehicle_csv", fallback=True)
        # grid_output = cfg.getboolean("output", "grid_time_series_csv", fallback=True)
        # plot_options = {"by_region": cfg.getboolean("output", "plot_grid_time_series_split", fallback=False),
        #                 "all_in_one": cfg.getboolean("output", "plot_grid_time_series_collective", fallback=False)}

        with open(pathlib.Path(scenario_path, cfg["files"]["vehicle_types"]), "r") as f:
            vehicle_types = json.load(f)

        cfg_dict = {  # "step_size": cfg.getint("basic", "stepsize"),
                    "soc_min": cfg.getfloat("basic", "soc_min"),
                    # "charging_threshold": cfg.getfloat("basic", "charging_threshold"),
                    "rng_seed": cfg["sim_params"].getint("seed", None),
                    "start_date": start_date,
                    "end_date": end_date
                    }
        num_threads = cfg.getint('sim_params', 'num_threads')

        return Simulation()
