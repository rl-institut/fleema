import src.advantage.vehicle as vehicle
import src.advantage.location as location
from src.advantage.util.conversions import step_to_timestamp
from src.advantage.spiceev_interface import get_spice_ev_scenario_dict

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2)
    car = vehicle.Vehicle(vehicle_type=car_type, soc=0.5)
    return car


@pytest.fixture()
def spot():
    spot = location.Location()
    return spot


@pytest.fixture()
def time_series():
    time_series = pd.date_range(datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 3), freq='min',
                                inclusive='left')
    return time_series


def test_call_spice_ev(car, time_series, spot):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    spice_dict = get_spice_ev_scenario_dict(car, spot, time_stamp, 10)
    assert "vehicles" in spice_dict["constants"].keys()
