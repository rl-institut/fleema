from advantage import location, vehicle


# each test is described in a function, the function must start with "test_"
# something has to be asserted within the function
def test_location():
    obj = location.Location("1", "available", "hpc")
    assert obj.type == "hpc"


def test_vehicle():
    vehicle_instance = vehicle.Vehicle(None, "idle", 1, True)
    assert vehicle_instance.availability
