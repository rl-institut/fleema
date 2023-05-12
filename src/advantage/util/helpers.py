"""This script includes general functions unrelated to any classes.

Functions
-------
deep_update

"""
import collections.abc
import os
import sys
import pandas as pd
import pathlib
import json


# see https://stackoverflow.com/questions/8391411/how-to-block-calls-to-print
# decorator used to block function printing to the console
def block_printing(func):
    def func_wrapper(*args, **kwargs):
        # block all printing to the console
        sys.stdout = open(os.devnull, "w")
        # call the method in question
        value = func(*args, **kwargs)
        # enable all printing to the console
        sys.stdout = sys.__stdout__
        # pass the return value of the method back
        return value

    return func_wrapper


def read_input_data(scenario_data_path, cfg):
    """
    Read input data files for a simulation scenario and return them as a dictionary of Pandas dataframes.

    Parameters
    ----------
    scenario_data_path : str or pathlib.Path
        The path to the directory containing the input data files.
    cfg : ConfigParser
        Contains the configuration parameters for the simulation scenario.

    Returns
    -------
    dict
        A dictionary containing the input data as Pandas dataframes, with keys corresponding to
        the names of the input data files.

    Raises
    ------
    FileNotFoundError
        If a specified file is not found in the specified directory and is not a 'temperature' or 'emission' file.

    Notes
    -----
    This function reads the following input data files:
    - 'schedule': A file containing the driving schedule data.
    - 'consumption': A file containing the vehicle energy consumption data.
    - 'distance': A file containing the distance data.
    - 'incline': A file containing the road incline data.
    - 'temperature': A file containing the outside temperature data (optional).
    - 'emission': A file containing the energy emission data (optional).

    The 'distance' and 'incline' files are expected to have an index column with the distance
    and incline values, respectively.
    """
    data_dict = {}
    files = [
        "schedule",
        "consumption",
        "distance",
        "incline",
        "temperature",
        "emission",
    ]
    index_col_files = ["distance", "incline"]
    for file in files:
        # read specified file
        file_path = pathlib.Path(scenario_data_path, cfg["files"][file])
        if not file_path.is_file():
            if file in ["temperature", "emission"]:
                data_dict[file] = None
                continue
            else:
                raise FileNotFoundError(
                    f"Specified file for {file} not found in path {file_path}"
                )
        if file in index_col_files:
            file_df = pd.read_csv(file_path, index_col=0)
        else:
            file_df = pd.read_csv(file_path)
        data_dict[file] = file_df

    # Add level_of_loading column to schedule
    with open(f"{scenario_data_path}/{cfg['files']['vehicle_types']}") as f:
        veh_types = json.load(f)["vehicle_types"]
    load_level = data_dict["schedule"]["occupation"] / data_dict["schedule"]["vehicle_type"].map(veh_types).str["capacity"]
    data_dict["schedule"]["level_of_loading"] = load_level.tolist()

    return data_dict


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place through recursion so only a key with its single value gets overwritten
    and not a nested dictionary.

    Parameters
    ----------
    source : dict
        Dictionary that receives the contents of overrides.
    overrides : dict
        Dictionary that writes its content into the source.

    Returns
    -------
    dict
        Updated Source.

    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source
