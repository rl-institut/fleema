import advantage.charger as charger

import pytest


@pytest.fixture()
def wallbox():
    point_list = [
        {},
        {}
    ]
    wallbox = charger.Charger("home_1", point_list)
    return wallbox


def test_constructor(wallbox):
    error_list = []
    if wallbox.name != "home_1":
        error_list.append(f"Charger name is {wallbox.name}, should be home_1")
    # TODO check for charging point properties
    assert not error_list,  "errors occured:\n{}".format("\n".join(error_list))


def test_num_charger(wallbox):
    assert wallbox.num_points == 2


def test_scenario_info(wallbox):
    assert wallbox.scenario_info["constants"]["charging_stations"]["home_1"]["max_power"] == 11
