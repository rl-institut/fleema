import advantage.vehicle as vehicle
from advantage.util.conversions import step_to_timestamp
from advantage.simulation_state import SimulationState

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2)
    car = vehicle.Vehicle("car", vehicle_type=car_type, soc=0.5)
    return car


@pytest.fixture()
def time_series():
    time_series = pd.date_range(datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 3), freq='min',
                                inclusive='left')
    return time_series


@pytest.fixture()
def sim_state():
    return SimulationState()


def test_constructor(sim_state: "SimulationState"):
    assert sim_state.charging_vehicles == []


def test_drive_result(car, time_series, sim_state: "SimulationState"):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.drive(time_stamp, start_step, 10, "station_1", 0.45, sim_state)
    assert sim_state.driving_vehicles[0] == car


def test_multi_drive(car, time_series, sim_state: "SimulationState"):
    for i in range(1, 5):
        start_step = 5 * i
        time_stamp = step_to_timestamp(time_series, start_step)
        car.drive(time_stamp, start_step, 10, "station_1", 0.45, sim_state)
    assert len(sim_state.driving_vehicles) == 1
