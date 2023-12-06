import fleema.location as location
import fleema.charger as charger
from fleema.event import Task, Status
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


@pytest.fixture()
def charging_task(parking_spot):
    return Task(0, 1, parking_spot, parking_spot, Status.CHARGING)


def test_constructor():
    obj = location.Location(name="school")
    assert obj.name == "school"


def test_grid(parking_spot):
    assert parking_spot.grid_connection


def test_charger(parking_spot):
    assert parking_spot.num_chargers


def test_available_charger():
    pass


def test_add_occupation(parking_spot):
    parking_spot.init_occupation(2)
    parking_spot.add_occupation(0, 1)
    assert not parking_spot.is_available(0, 0)


def test_add_occupation_from_event(parking_spot, charging_task):
    parking_spot.init_occupation(2)
    parking_spot.add_occupation_from_event(charging_task)
    assert not parking_spot.is_available(0, 0)


def test_occupation(parking_spot):
    parking_spot.init_occupation(2)
    assert parking_spot.is_available(0, 0)
