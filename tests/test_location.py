import advantage.location as location
import pytest


@pytest.fixture()
def parking_spot():
    parking_spot = location.Location(grid_info={})
    return parking_spot


def test_constructor():
    obj = location.Location(type="hpc")
    assert obj.type == "hpc"


def test_charger(parking_spot):
    assert parking_spot.has_charger()


def test_grid(parking_spot):
    assert parking_spot.has_grid_connection()
