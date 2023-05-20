from advantage.ride import RideCalc
from advantage.location import Location
from advantage.vehicle import VehicleType
import pandas as pd
import pytest
import pathlib


@pytest.fixture()
def driving_sim():
    cons = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv"))
    dist = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "distance.csv"), index_col=0)
    incl = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "incline.csv"), index_col=0)
    temp = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv"))
    return RideCalc(cons, dist, incl, temp, "median")


@pytest.fixture()
def driving_sim_bad_temperature_option():
    cons_path = pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv")
    cons = pd.read_csv(cons_path)
    temp_path = pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv")
    temp = pd.read_csv(temp_path)
    return RideCalc(cons, cons, cons, temp, "bad_column")


@pytest.fixture()
def location_a():
    return Location("Marktplatz")


@pytest.fixture()
def location_b():
    return Location("Artrium")


@pytest.fixture()
def vehicle_type_ez10():
    return VehicleType("EZ10")


def test_get_nearest_unique_basic(driving_sim):
    assert driving_sim.get_nearest_uniques(0, 1) == (0, 0)
    assert driving_sim.get_nearest_uniques(0.1, 1) == (0, 0.25)
    assert driving_sim.get_nearest_uniques(1, 1) == (1, 1)


def test_get_nearest_unique_outer_boundaries(driving_sim):
    assert driving_sim.get_nearest_uniques(-1, 1) == (0, 0)
    assert driving_sim.get_nearest_uniques(2, 1) == (1, 1)


# get_consumption
def test_get_consumption_basic(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -12, 2.626) * -1 == 1.886
    res = [
        driving_sim.get_consumption("EZ10", 0, -0.04, -temp, 2.626) * -1
        for temp in [15.9, 15, 14, 13, 12.5, 12.1]
    ]
    for v in res:
        assert 1.886 < v < 2.13


# get_consumption: vehicle type name
def test_get_consumption_vehicle_type_wrong_data_type(driving_sim):
    with pytest.raises(TypeError):
        driving_sim.get_consumption(0, 0, -0.04, -12, 2.626)


def test_get_consumption_vehicle_type_doesnt_exist(driving_sim):
    with pytest.raises(ValueError):
        driving_sim.get_consumption("M18", 0, -0.04, -12, 2.626)


# get_consumption: load_level
def test_get_consumption_load_level_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 2, -0.04, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", -1, -0.04, -16, 2.626) * -1 == 2.13


def test_get_consumption_load_level_input_string(driving_sim):
    assert driving_sim.get_consumption("EZ10", "string", -0.04, -16, 2.626) * -1 == 2.13


# get_consumption: incline
def test_get_consumption_incline_wrong_data_type(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, "string", -16, 2.626) * -1 == 2.176


def test_get_consumption_incline_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -1, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, 1, -16, 2.626) * -1 == 2.304


# get_consumption: speed
def test_get_consumption_speed_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 0) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 100) * -1 == 0.349


def test_get_consumption_speed_wrong_data_type(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, "string") * -1 == 0.808


# get_consumption: temperature
def test_get_consumption_temperature_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -100, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, 100, 2.626) * -1 == 0.516


def test_get_consumption_temperature_wrong_data_type(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, "string", 2.626) * -1 == 0.487


# get_temperature
def test_get_temperature_basic(driving_sim):
    assert driving_sim.get_temperature("2022-01-01 01:01:00") == 12.9
    assert driving_sim.get_temperature("1999-01-01 00:01:00") == 13.3
    assert driving_sim.get_temperature("2022-01-01 13:30:00") == 20.5


def test_get_temperature_wrong_string_format(driving_sim):
    assert driving_sim.get_temperature("2022-01-01T16:30:00") == 19.6


def test_get_temperature_bad_option(driving_sim_bad_temperature_option):
    assert driving_sim_bad_temperature_option.get_temperature("2022-01-01 16:30:00") == 5.2


def test_get_temperature_bad_option_wrong_string_format(
    driving_sim_bad_temperature_option,
):
    assert driving_sim_bad_temperature_option.get_temperature("2022-01-01T16:30:00") == 6.3


# get_location_values
def test_get_location_values_basic(driving_sim, location_a, location_b):
    assert driving_sim.get_location_values(location_a, location_a) == (0, 0)
    assert driving_sim.get_location_values(location_a, location_b) == (0.370, 0)


def test_get_location_values_type_error(driving_sim, location_a):
    with pytest.raises(TypeError):
        driving_sim.get_location_values(1, location_a)
    with pytest.raises(TypeError):
        driving_sim.get_location_values(location_a, 1)


# calculate_consumption
def test_calculate_consumption_basic(driving_sim, vehicle_type_ez10):
    assert driving_sim.calculate_consumption(vehicle_type_ez10, -0.04, -16, 2.626, 0, 0) == (0, 0)
    assert driving_sim.calculate_consumption(vehicle_type_ez10, -0.04, -16, 2.626, 0, 1) == (-2.13, -0.0426)


def test_calculate_consumption_wrong_type(driving_sim, vehicle_type_ez10):
    with pytest.raises(TypeError):
        assert driving_sim.calculate_consumption("vehicle_type_ez10", -0.04, -16, 2.626, 0, 0) == (0, 0)
