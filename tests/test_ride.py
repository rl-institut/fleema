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
    defaults = {"load_level": 0, "incline": 0, "distance": 0, "temperature": 20, "speed": 8.65}
    return RideCalc(cons, dist, incl, temp, "median", defaults)


@pytest.fixture()
def driving_sim_bad_temperature_option():
    cons_path = pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv")
    cons = pd.read_csv(cons_path)
    temp_path = pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv")
    temp = pd.read_csv(temp_path)
    defaults = {"load_level": 0, "incline": 0, "distance": 0, "temperature": 20, "speed": 8.65}
    return RideCalc(cons, cons, cons, temp, "bad_column", defaults)


@pytest.fixture()
def location_a():
    return Location("Marktplatz")


@pytest.fixture()
def location_b():
    return Location("Artrium")


@pytest.fixture()
def vehicle_type_ez10():
    return VehicleType("EZ10")


@pytest.fixture()
def data_table(driving_sim):
    df = driving_sim.consumption_table
    inc_col = df["incline"]
    tmp_col = df["t_amb"]
    lol_col = df["level_of_loading"]
    speed_col = df["mean_speed"]
    cons_col = df["consumption"]
    return list(zip(lol_col, inc_col, speed_col, tmp_col, cons_col))


# nd_interp
def test_nd_interp_basic_load_level(driving_sim, data_table):
    assert driving_sim.nd_interp((0, -0.04, 2.626, -16), data_table) == 2.13
    assert driving_sim.nd_interp((0.25, 0.01, 2.626, 8), data_table) == 0.933


def test_nd_interp_too_low_load_level(driving_sim, data_table):
    assert driving_sim.nd_interp((-1, -0.04, 2.626, -16), data_table) == 2.13


def test_nd_interp_too_high_load_level(driving_sim, data_table):
    assert driving_sim.nd_interp((2, -0.04, 2.626, -16), data_table) == 1.755


def test_nd_interp_too_high_load_level_incline(driving_sim, data_table):
    assert driving_sim.nd_interp((2, 1, 2.626, -16), data_table) == 2.031


def test_nd_interp_too_high_load_level_incline_speed_temperature(driving_sim, data_table):
    assert driving_sim.nd_interp((2, 1, 50, 50), data_table) == 0.474


# get_nearest_unique
def test_get_nearest_unique_basic_load_level(driving_sim):
    assert driving_sim.get_nearest_uniques(0, 1) == (0, 0)
    assert driving_sim.get_nearest_uniques(0.1, 1) == (0, 0.25)
    assert driving_sim.get_nearest_uniques(1, 1) == (1, 1)


def test_get_nearest_unique_outer_boundaries_load_level(driving_sim):
    assert driving_sim.get_nearest_uniques(-1, 1) == (0, 0)
    assert driving_sim.get_nearest_uniques(2, 1) == (1, 1)


# get_consumption
def test_get_consumption_basic(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -12, 2.626) * -1 == 1.886


def test_get_consumption_interpolation(driving_sim):
    res = [driving_sim.get_consumption("EZ10", 0, -0.04, -temp, 2.626) * -1 for temp in [15.9, 15, 14, 13, 12.5, 12.1]]
    for v in res:
        assert 1.886 < v < 2.13


# get_consumption: load_level
def test_get_consumption_load_level_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 2, -0.04, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", -1, -0.04, -16, 2.626) * -1 == 2.13


def test_get_consumption_load_level_input_string(driving_sim):
    with pytest.raises(TypeError):
        driving_sim.get_consumption("EZ10", "string", -0.04, -16, 2.626)


# get_consumption: incline
def test_get_consumption_incline_wrong_data_type(driving_sim):
    with pytest.raises(TypeError):
        driving_sim.get_consumption("EZ10", 0, "string", -16, 2.626)


def test_get_consumption_incline_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -1, -16, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, 1, -16, 2.626) * -1 == 2.304


# get_consumption: speed
def test_get_consumption_speed_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 0) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -16, 100) * -1 == 0.349


def test_get_consumption_speed_wrong_data_type(driving_sim):
    with pytest.raises(TypeError):
        driving_sim.get_consumption("EZ10", 0, -0.04, -16, "string")


# get_consumption: temperature
def test_get_consumption_temperature_out_of_bounds(driving_sim):
    assert driving_sim.get_consumption("EZ10", 0, -0.04, -100, 2.626) * -1 == 2.13
    assert driving_sim.get_consumption("EZ10", 0, -0.04, 100, 2.626) * -1 == 0.516


def test_get_consumption_temperature_wrong_data_type(driving_sim):
    with pytest.raises(TypeError):
        driving_sim.get_consumption("EZ10", 0, -0.04, "string", 2.626)


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


# calculate_consumption
def test_calculate_consumption_basic(driving_sim, vehicle_type_ez10):
    assert driving_sim.calculate_consumption(vehicle_type_ez10, -0.04, -16, 2.626, 0, 0) == (0, 0)
    assert driving_sim.calculate_consumption(vehicle_type_ez10, -0.04, -16, 2.626, 0, 1) == (-2.13, -0.0426)


def test_calculate_consumption_negative_distance(driving_sim, vehicle_type_ez10):
    with pytest.raises(ValueError):
        driving_sim.calculate_consumption(vehicle_type_ez10, -0.04, -16, 2.626, 0, -1)


# calculate_trip
def test_calculate_trip_basic(driving_sim, location_a, location_b, vehicle_type_ez10):
    assert driving_sim.calculate_trip(location_a, location_a, vehicle_type_ez10, 0) == {
        "consumption": 0,
        "soc_delta": 0,
        "trip_time": 0,
    }
    assert driving_sim.calculate_trip(location_a, location_a, vehicle_type_ez10, 100) == {
        "consumption": 0,
        "soc_delta": 0,
        "trip_time": 0,
    }
    assert driving_sim.calculate_trip(location_a, location_b, vehicle_type_ez10, 1, "2022-01-01 04:00:00") == {
        "consumption": -0.37 * 0.757,
        "soc_delta": -0.37 * 0.757 / vehicle_type_ez10.battery_capacity,
        "trip_time": 22.2,
    }


def test_ride_calc_basic():
    cons = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv"))
    dist = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "distance.csv"), index_col=0)
    incl = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "incline.csv"), index_col=0)
    temp = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv"))
    defaults = {"load_level": 0, "incline": 0, "distance": 0, "temperature": 20, "speed": 8.65}
    assert RideCalc(cons, dist, incl, temp, "median", defaults)


def test_ride_calc_speed_zero():
    cons = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv"))
    dist = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "distance.csv"), index_col=0)
    incl = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "incline.csv"), index_col=0)
    temp = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv"))
    defaults = {"load_level": 0, "incline": 0, "distance": 0, "temperature": 20, "speed": 0}
    with pytest.raises(ValueError):
        RideCalc(cons, dist, incl, temp, "median", defaults)


def test_ride_calc_speed_negative():
    cons = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv"))
    dist = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "distance.csv"), index_col=0)
    incl = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "incline.csv"), index_col=0)
    temp = pd.read_csv(pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv"))
    defaults = {"load_level": 0, "incline": 0, "distance": 0, "temperature": 20, "speed": -1}
    with pytest.raises(ValueError):
        RideCalc(cons, dist, incl, temp, "median", defaults)
