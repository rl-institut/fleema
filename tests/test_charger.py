import advantage.charger as charger

import pytest


@pytest.fixture()
def wallbox():
    point_list = [
        charger.ChargingPoint("home_1_0", ["Type2", "Schuko"], [11, 3.7], "conductive")
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
    assert wallbox.num_points == 1


def test_scenario_info(wallbox):
    i = wallbox.scenario_info_by_plugs(["Type2", "Schuke", "ChaDeMo"])
    assert i["constants"]["charging_stations"]["home_1_0"]["max_power"] == 11


def test_scenario_info_no_charging_points():
    ch = charger.Charger("charger", [])
    with pytest.raises(ValueError, match="Scenario dictionary requested of charger charger with no charging points"):
        ch.scenario_info_by_plugs(["Schuko"])
