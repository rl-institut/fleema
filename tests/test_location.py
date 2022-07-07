import advantage.location as location
import advantage.charger as charger
import pytest


# neue location erzeugen, absichtlich falsch (zB. vehicle in charger liste)
@pytest.fixture()
def parking_spot():
    parking_spot = location.Location(grid_info={}, chargers=[charger.Charger(name="charger_1")])
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
    assert parking_spot.availability()


def test_available_charger():
    pass
#
# def test_power(grid, charging_point):
#
#
#
#
# def
#
#
#
# def test_allocation():
#
#
