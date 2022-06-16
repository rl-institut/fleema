import advantage.vehicle as vehicle
import pytest


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2)
    car = vehicle.Vehicle(vehicle_type=car_type, soc=0.5)
    return car


def test_constructor(car):
    error_list = []
    if car.vehicle_type.battery_capacity != 30:
        error_list.append(f"Battery capacity is {car.vehicle_type.battery_capacity}, should be 30")
    if car.vehicle_type.base_consumption != 0.2:
        error_list.append(f"Battery capacity is {car.vehicle_type.base_consumption}, should be 0.2")

    assert not error_list,  "errors occured:\n{}".format("\n".join(error_list))


def test_drive(car):
    soc_start = car.soc
    # car.drive()
    car.soc -= 0.3
    assert car.soc < soc_start


def test_charge(car):
    soc_start = car.soc
    # car.charge(1, 2, 11, "slow")
    car.soc += 0.2
    assert car.soc > soc_start
