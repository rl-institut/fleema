import src.advantage.vehicle as vehicle
from src.advantage.util.conversions import step_to_timestamp

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2)
    car = vehicle.Vehicle(vehicle_type=car_type, soc=0.5)
    return car


@pytest.fixture()
def time_series():
    time_series = pd.date_range(datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 3), freq='min',
                                inclusive='left')
    return time_series


def test_timestamp_conversion(time_series):
    start_step = 75
    time_stamp = step_to_timestamp(time_series, start_step)
    assert time_stamp == datetime.datetime(2022, 1, 1, 1, 15)


def test_constructor(car):
    error_list = []
    if car.vehicle_type.battery_capacity != 30:
        error_list.append(f"Battery capacity is {car.vehicle_type.battery_capacity}, should be 30")
    if car.vehicle_type.base_consumption != 0.2:
        error_list.append(f"Battery capacity is {car.vehicle_type.base_consumption}, should be 0.2")
    if car.usable_soc != 0.5:
        error_list.append(f"Battery capacity is {car.vehicle_type.base_consumption}, should be 0.5")

    assert not error_list,  "errors occured:\n{}".format("\n".join(error_list))


def test_drive(car):
    soc_start = car.soc
    # car.drive()
    car.soc -= 0.3
    assert car.soc < soc_start


def test_charge_result(car, time_series):
    # charge gets called with time, charging station power, charging type and station efficiency
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.charge(time_stamp, start_step, time=60, power=11, new_soc=0.8)
    assert car.soc == 0.8


def test_charge_bad_soc(car, time_series):
    # charge gets called with time, charging station power, charging type and station efficiency
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError):
        car.charge(time_stamp, start_step, time=60, power=11, new_soc=0.3)


def test_charge_too_much_energy(car, time_series):
    # charge gets called with time, charging station power, charging type and station efficiency
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError):
        car.charge(time_stamp, start_step, time=2, power=7, new_soc=0.9)


def test_charge_input_checks(car, time_series):
    # charge gets called with time, charging station power, charging type and station efficiency
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError):
        car.charge(time_stamp, start_step, time="-1", power=11, new_soc=0.8)
