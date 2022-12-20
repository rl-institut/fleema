import advantage.location as location
import advantage.charger as charger
import pytest


@pytest.fixture()
def parking_spot():
    # TODO input actual values for Charger
    parking_spot = location.Location(
        grid_info={}, chargers=[charger.Charger("charger_1", [])]
    )
    return parking_spot


@pytest.fixture()
def grid():
    grid = location.Location(grid_info={})
    return grid


def test_constructor():
    obj = location.Location(name="school")
    assert obj.name == "school"


def test_grid(parking_spot):
    assert parking_spot.grid_connection


def test_charger(parking_spot):
    assert parking_spot.num_chargers


# def test_availability(parking_spot):
#     assert parking_spot.availability()


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
