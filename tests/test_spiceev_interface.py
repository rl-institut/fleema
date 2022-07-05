import advantage.vehicle as vehicle
import advantage.location as location
import advantage.charger as charger
from advantage.util.conversions import step_to_timestamp
from advantage.spiceev_interface import get_spice_ev_scenario_dict, run_spice_ev

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2,
                                   charging_curve=[[0, 11], [0.8, 11], [1, 11]])
    car = vehicle.Vehicle(vehicle_type=car_type, soc=0.5)
    return car


@pytest.fixture()
def spot():
    charge_spot = charger.Charger()
    spot = location.Location(chargers=[charge_spot], grid_info={"max_power": 150})
    return spot


@pytest.fixture()
def time_series():
    time_series = pd.date_range(datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 3), freq='min',
                                inclusive='left')
    return time_series


def test_create_dict(car, time_series, spot):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    spice_dict = get_spice_ev_scenario_dict(car, spot, time_stamp, 10)
    error_list = []
    if "vehicles" not in spice_dict["constants"].keys():
        error_list.append("Vehicles is not in constants.")
    if "vehicle_types" not in spice_dict["constants"].keys():
        error_list.append("Vehicle_types is not in constants.")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))


def test_run_spice_ev(car, time_series, spot):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    spice_dict = get_spice_ev_scenario_dict(car, spot, time_stamp, 10)
    run_spice_ev(spice_dict, "balanced")
