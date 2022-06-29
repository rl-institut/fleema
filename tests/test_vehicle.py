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


def test_drive_result(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.drive(time_stamp, start_step, time=10, destination="station_1", new_soc=0.45)
    assert car.soc == 0.45


def test_drive_bad_soc(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError, match="SoC of vehicle can't be higher after driving."):
        car.drive(time_stamp, start_step, time=60, destination="station_1", new_soc=0.7)


def test_drive_sanity(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError, match="Consumption too high."):
        car.drive(time_stamp, start_step, time=2, destination="station_1", new_soc=0.1)


def test_drive_input_checks(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError, match="Argument has wrong type."):
        car.charge(time_stamp, start_step, time="-1", power=11, new_soc=0.8)


def test_charge_result(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.charge(time_stamp, start_step, time=60, power=11, new_soc=0.8)
    assert car.soc == 0.8


def test_charge_bad_soc(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError, match="SoC of vehicle can't be lower after charging."):
        car.charge(time_stamp, start_step, time=60, power=11, new_soc=0.3)


def test_charge_sanity(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(ValueError, match="SoC can't be reached in specified time window with given power."):
        car.charge(time_stamp, start_step, time=2, power=7, new_soc=0.9)


def test_charge_input_checks(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError, match="Argument has wrong type."):
        car.charge(time_stamp, start_step, time="-1", power=11, new_soc=0.8)


def test_park_result(car, time_series):
    output_size = len(car.output["timestamp"])
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.park(time_stamp, start_step, 10)
    assert output_size + 1 == len(car.output["timestamp"])


def test_park_input_checks(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError, match="Argument has wrong type."):
        car.park(time_stamp, start_step, "-1")


def test_scenario_info(car):
    assert car.scenario_info["vehicle_name_0"]["soc"] == 0.5

#  TODO use in code: spice_ev_scenario["constants"]["vehicles"].update(car.scenario_info)
