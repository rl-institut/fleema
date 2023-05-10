from advantage.ride import RideCalc
from advantage.location import Location
import pandas as pd
import pytest
import pathlib


@pytest.fixture()
def driving_sim():
    cons_path = pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv")
    cons = pd.read_csv(cons_path)
    temp_path = pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv")
    temp = pd.read_csv(temp_path)
    return RideCalc(cons, cons, cons, temp, "median")  # TODO add inclines/distances


@pytest.fixture()
def driving_sim_bad_temperature_option():
    cons_path = pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv")
    cons = pd.read_csv(cons_path)
    temp_path = pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv")
    temp = pd.read_csv(temp_path)
    return RideCalc(cons, cons, cons, temp, "bad_column")


def test_get_consumption(driving_sim):
    # TODO change for new consumption table
    """error_list = []
    if not -49.706 == driving_sim.get_consumption("bus_18m", -0.04, -10, 2.626, 0.0):
        error_list.append("First result is wrong")
    if not -1.163 == driving_sim.get_consumption("atlas_7m", 0.04, 20, 37.093, 0.9):
        error_list.append("Second result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.04, -12.5, 2.626, 0.0)
    if not -62.502 < consumption < -49.706:
        error_list.append("Third result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.03, 0.0, 2.626, 0.0)
    if not -28.303 < consumption < -28.154:
        error_list.append("Fourth result is wrong")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))"""


def test_get_temperature_basic(driving_sim):
    assert driving_sim.get_temperature("2022-01-01 01:01:00") == 12.9
    assert driving_sim.get_temperature("1999-01-01 00:01:00") == 13.3
    assert driving_sim.get_temperature("2022-01-01 13:30:00") == 20.5


def test_get_temperature_wrong_string_format(driving_sim):
    assert driving_sim.get_temperature("2022-01-01T16:30:00") == 19.6


def test_get_temperature_bad_option(driving_sim_bad_temperature_option):
    assert driving_sim_bad_temperature_option.get_temperature("2022-01-01 16:30:00") == 5.2


def test_get_temperature_bad_option_wrong_string_format(driving_sim_bad_temperature_option):
    assert driving_sim_bad_temperature_option.get_temperature("2022-01-01T16:30:00") == 6.3


def test_load_level_basic(driving_sim):
    assert driving_sim.get_consumption("EZ10", -0.04, -16, 2.626, 0.0) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", -0.03, -2, 17.957, 0.5) * -1 == 0.308


def test_load_level_input_bigger_one(driving_sim):
    assert driving_sim.get_consumption("EZ10", -0.04, -16, 2.626, 2) * -1 == 2.13


def test_load_level_input_smaller_one(driving_sim):
    assert driving_sim.get_consumption("EZ10", -0.04, -16, 2.626, -1) * -1 == 2.13


def test_load_level_input_string(driving_sim):
    assert driving_sim.get_consumption("EZ10", -0.04, -16, 2.626, "0") * -1 == 2.13
