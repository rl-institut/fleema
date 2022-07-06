import advantage.location as location
import pytest

# neue location erzeugen, absichtlich falsch (zB. vehicle in charger liste)
@pytest.fixture()
def parking_spot():
    parking_spot = location.Location(grid_info={})
    return parking_spot

@pytest.fixture()
def charging_point():
    charging_point = location.Location(peak_power=300)
    return charging_point

@pytest.fixture()
def grid():
    grid = location.Location(grid_info={})
    return grid

def test_constructor():
    obj = location.Location(type="hpc")
    assert obj.type == "hpc"

def test_grid(parking_spot):
    assert parking_spot.has_grid_connection()

def test_charger(parking_spot):
    assert parking_spot.has_charger()

def test_availability(parking_spot):
    error_list = []
    if parking_spot.availability = False
        error_list.append(f"All charging points are occupied")
    elif parking_spot.availability = True
        print(f"At least one charging point available")

def test_available_charger():
    list_charger = []
    if location.Location(self.status) == "available"
        list_charger.append(self.location_id)

def test_power(grid, charging_point):




def



def test_allocation():


