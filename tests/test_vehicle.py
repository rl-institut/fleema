import advantage.vehicle as vehicle
import pytest


@pytest.fixture(scope='session')
def car():
    car_type = vehicle.VehicleType(battery_capacity=30, base_consumption=0.2)
    car = vehicle.Vehicle(vehicle_type=car_type, soc=0.5)
    return car


def test_constructor():
    bus_type = vehicle.VehicleType(battery_capacity=100, base_consumption=0.4)
    bus = vehicle.Vehicle(vehicle_type=bus_type, soc=1, availability=True)
    assert bus.vehicle_type.battery_capacity == 100


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
