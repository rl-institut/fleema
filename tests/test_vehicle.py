import advantage.vehicle as vehicle


def test_charge():
    car_type = vehicle.VehicleType()
    car = vehicle.Vehicle(starting_soc=0.5)
    car.charge(1, 2, 11, "slow")
    assert car.soc > car.soc_start
