from fleema.vehicle import Vehicle, VehicleType
from fleema.event import Task, Status
from fleema.location import Location
from fleema.util.conversions import step_to_timestamp

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car() -> Vehicle:
    car_type = VehicleType(battery_capacity=30, base_consumption=0.2)
    car = Vehicle("car", vehicle_type=car_type, soc=0.5, status=Status.DRIVING)
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


def test_timestamp_conversion(time_series):
    start_step = 75
    time_stamp = step_to_timestamp(time_series, start_step)
    assert time_stamp == datetime.datetime(2022, 1, 1, 1, 15)


def test_constructor(car):
    error_list = []
    if car.vehicle_type.battery_capacity != 30:
        error_list.append(
            f"Battery capacity is {car.vehicle_type.battery_capacity}, should be 30"
        )
    if car.vehicle_type.base_consumption != 0.2:
        error_list.append(
            f"Battery capacity is {car.vehicle_type.base_consumption}, should be 0.2"
        )
    if car.usable_soc != 0.3:
        error_list.append(f"Battery capacity is {car.usable_soc}, should be 0.3")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))


def test_drive_result(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.drive(time_stamp, start_step, 10, Location(), 0.45, 1)
    assert car.soc == 0.45


def test_drive_bad_soc(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(
        ValueError, match="SoC of vehicle can't be higher after driving."
    ):
        car.drive(time_stamp, start_step, 60, Location(), 0.7, 1)


# def test_drive_sanity(car, time_series):
#     start_step = 5
#     time_stamp = step_to_timestamp(time_series, start_step)
#     with pytest.raises(ValueError, match="Consumption too high."):
#        car.drive(time_stamp, start_step, time=2, destination="station_1", new_soc=0.1)


def test_drive_input_checks(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError, match="Argument has wrong type."):
        car.drive(time_stamp, start_step, "60", Location(), 0.7, 1)


def test_charge_result(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    car.charge(time_stamp, start_step, 60, 11, 0.8, 11)
    assert car.soc == 0.8


def test_charge_bad_soc(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(
        ValueError, match="SoC of vehicle can't be lower after charging."
    ):
        car.charge(
            time_stamp, start_step, time=60, power=11, new_soc=0.3, charging_capacity=11
        )


def test_charge_sanity(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(
        ValueError,
        match="SoC can't be reached in specified time window with given power.",
    ):
        car.charge(
            time_stamp, start_step, time=2, power=7, new_soc=0.9, charging_capacity=11
        )


def test_charge_input_checks(car, time_series):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    with pytest.raises(TypeError, match="Argument has wrong type."):
        car.charge(
            time_stamp,
            start_step,
            time="-1",
            power=11,
            new_soc=0.8,
            charging_capacity=11,
        )


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
    assert car.scenario_info["components"]["vehicles"]["car"]["soc"] == 0.5


def test_task_list_sanity(car):
    location_1 = Location("location_1")
    location_2 = Location("location_2")
    task_1 = Task(0, 1, location_1, location_2, Status.DRIVING)
    task_2 = Task(2, 4, location_2, location_2, Status.CHARGING)
    task_3 = Task(5, 6, location_2, location_1, Status.DRIVING)
    for task in [task_1, task_2, task_3]:
        car.add_task(task)

    assert car.has_valid_task_list


def test_incorrect_task_list(car):
    location_1 = Location("location_1")
    location_2 = Location("location_2")
    task_1 = Task(0, 1, location_1, location_1, Status.DRIVING)
    task_2 = Task(2, 4, location_2, location_2, Status.CHARGING)
    task_3 = Task(5, 6, location_2, location_1, Status.DRIVING)
    for task in [task_1, task_2, task_3]:
        car.add_task(task)

    assert not car.has_valid_task_list
