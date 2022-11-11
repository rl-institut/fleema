"""This script includes the Simulation class.

Classes
-------
Simulation
"""

import configparser as cp
import math
import pathlib
import pandas as pd
import json

from advantage.location import Location
import advantage.vehicle as vehicle
from advantage.charger import Charger, PlugType
from advantage.simulation_state import SimulationState

from advantage.util.conversions import date_string_to_datetime


class Simulation:
    """This class can import a specified config directory and build a Simulation out of the given scenario.

    It also contains the run function, which starts the simulation.

    Attributes
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
    plug_types_ dict
        Dictionary with strings of the plug-type and dictionaries comprised of the name, capacity and charging_type
        as values.

    """

    def __init__(self, schedule, vehicle_types, charging_points, cfg_dict, consumption, trips):
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
        self.num_threads = cfg_dict["num_threads"]

        self.schedule = schedule

        # driving simulation
        self.consumption = consumption
        self.trips = trips

        # use other args to create objects
        self.vehicle_types = {}
        for name, info in vehicle_types.items():
            self.vehicle_types[name] = vehicle.VehicleType(name, info["capacity"], self.soc_min, 0,
                                                           info["charging_power"], info["charging_curve"],
                                                           self.min_charging_power)

        self.locations = {}
        for location_name in self.schedule.departure_name.unique():
            self.locations[location_name] = Location(location_name)

        self.plug_types = {}
        for name, info in charging_points["plug_types"].items():
            self.plug_types[name] = PlugType(name, info["capacity"], info["plug"])
        for name, info in charging_points["charging_points"].items():
            # TODO add chargers to locations based on charging_points
            plug_types = [p for p in self.plug_types.values() if p.name in info["plug_types"]]
            charger = Charger.from_json(name, info["number_charging_points"], plug_types)
            self.locations[name].chargers.append(charger)

        # Instantiation of observer
        self.observer = SimulationState()

    def run(self):
        # TODO create initial charging schedules / tasks (where?)
        # TODO start fleet management (includes loop)

        pass

    def interpolate_consumption(self, incline, temperature, distance, sp_type=8.65, level_of_loading=0.):
        # extract possible rows from consumption_df
        # find the 2 points to interpolate

        rows = self.consumption['incline']

        # reductions
        rows = self._nearest_rows(rows, incline)
        rows = self._nearest_rows(rows, temperature)
        rows = self._nearest_rows(rows, distance)
        rows = self._nearest_rows(rows, sp_type)
        rows = self._nearest_rows(rows, level_of_loading)

        # real interpolation between the rows which remain
        consumption_index = 0

        return self.consumption['consumption'][consumption_index]

    def _nearest_rows(self, rows, param):
        from decimal import Decimal
        return_rows = None
        rows_values = rows.tolist()
        # if param has an exact value like in the consumption table
        if param in rows_values:
            return rows.loc[lambda x: x == param]

        smallest_gap_minus = math.inf
        smallest_gap_plus = math.inf
        for i in range(len(rows_values)):
            if rows_values[i] < param:
                gap_minus = param - rows_values[i]
                if gap_minus < smallest_gap_minus:
                    smallest_gap_minus = round(gap_minus, 2)
            if rows_values[i] > param:
                gap_plus = float(rows_values[i] - param)
                if gap_plus < smallest_gap_plus:
                    smallest_gap_plus = round(gap_plus, 2)

        minus_value = round(param + smallest_gap_minus*.1, 2)
        plus_value = round(param + smallest_gap_plus, 2)
        row_minus = rows.loc[lambda x: x == minus_value]
        row_plus = rows.loc[lambda x: x == plus_value]

        print(minus_value)
        print(plus_value)
        print()
        print(row_minus)
        print(row_plus)

        print(rows.to_string())


        return return_rows


    @classmethod
    def from_config(cls, scenario_name):
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
            Simulation object

        Raises
        ------
        FileNotFoundError
            If the scenario is not found in the ./scenarios directory.
            If the config file scenario.cfg is not found or can't be read..

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

        # read consumption_table
        consumption_path = pathlib.Path(scenario_path, "consumption.csv")
        consumption_df = pd.read_csv(consumption_path)

        # read trips
        trips_table = pathlib.Path(scenario_path, "trips.csv")
        trips_df = pd.read_csv(trips_table)

        return Simulation(schedule, vehicle_types, charging_points, cfg_dict, consumption_df, trips_df)
