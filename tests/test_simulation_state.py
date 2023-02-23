import advantage.vehicle as vehicle
from advantage.util.conversions import step_to_timestamp
from advantage.simulation_state import SimulationState
from advantage.location import Location
from advantage.event import Status

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
    time_series = pd.date_range(
        datetime.datetime(2022, 1, 1),
        datetime.datetime(2022, 1, 3),
        freq="min",
        inclusive="left",
    )
    return time_series


@pytest.fixture()
def sim_state():
    return SimulationState()


def test_constructor(sim_state):
    assert sim_state.charging_vehicles == []


def test_drive_result(car, time_series, sim_state):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.drive(time_stamp, start_step, 10, Location(), 0.45, 1, observer=sim_state)
    assert sim_state.driving_vehicles[0] == car


def test_multi_drive(car, time_series, sim_state):
    for i in range(1, 5):
        start_step = 5 * i
        time_stamp = step_to_timestamp(time_series, start_step)
        car.drive(time_stamp, start_step, 10, Location(), 0.45, 1, observer=sim_state)
    assert len(sim_state.driving_vehicles) == 1


def test_remove_vehicle(car, sim_state):
    sim_state.driving_vehicles.append(car)
    sim_state.parking_vehicles.append(car)
    sim_state.charging_vehicles.append(car)
    sim_state.remove_vehicle(car)
    error_list = []
    if car in sim_state.driving_vehicles:
        error_list.append("Vehicle still in driving list")
    if car in sim_state.parking_vehicles:
        error_list.append("Vehicle still in parking list")
    if car in sim_state.charging_vehicles:
        error_list.append("Vehicle still in charging list")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))


def test_remove_multi_vehicle(car, sim_state):
    for i in range(5):
        sim_state.driving_vehicles.append(car)
    sim_state.remove_vehicle(car)
    assert car not in sim_state.driving_vehicles


def test_update_vehicle_drive(car, sim_state):
    car.status = Status.DRIVING
    sim_state.update_vehicle(car)
    assert car in sim_state.driving_vehicles


def test_update_vehicle_charge(car, sim_state):
    car.status = Status.CHARGING
    sim_state.update_vehicle(car)
    assert car in sim_state.charging_vehicles


def test_update_vehicle_park(car, sim_state):
    car.status = Status.PARKING
    sim_state.update_vehicle(car)
    assert car in sim_state.parking_vehicles

def test_add_to_accumulated_results(sim_state):

    # test adding a new key-value pair to the accumulated results
    sim_state.add_to_accumulated_results("key1", 10.5)
    assert sim_state.accumulated_results == {"key1": 10.5}

    # test adding a value to an existing key
    sim_state.add_to_accumulated_results("key1", 3.5)
    assert sim_state.accumulated_results == {"key1": 14.0}

    # test rounding of the accumulated value to 4 decimal places
    sim_state.add_to_accumulated_results("key1", 1.23456789)
    assert sim_state.accumulated_results == {"key1": 15.2346}

    # test adding a new key-value pair with a negative value
    sim_state.add_to_accumulated_results("key2", -5.5)
    assert sim_state.accumulated_results == {"key1": 15.2346, "key2": -5.5}
