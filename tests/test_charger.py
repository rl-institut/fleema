import advantage.charger as charger

import pytest


@pytest.fixture()
def wallbox():
    point_list = [
        charger.ChargingPoint("home_1_0", [charger.PlugType("Type2_11", 11, "Type2")])
    ]
    wallbox = charger.Charger("home_1", point_list)
    return wallbox


def test_constructor(wallbox):
    error_list = []
    if wallbox.name != "home_1":
        error_list.append(f"Charger name is {wallbox.name}, should be home_1")
    # TODO check for charging point properties
    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))


def test_num_charger(wallbox):
    assert wallbox.num_points == 1


def test_scenario_info(wallbox):
    i = wallbox.get_scenario_info("home_1_0", ["Type2", "Schuko", "ChaDeMo"])
    assert i["components"]["charging_stations"]["home_1_0"]["max_power"] == 11


def test_scenario_info_wrong_id(wallbox):
    with pytest.raises(
        ValueError, match="Point ID home doesn't match any Points in charger home_1"
    ):
        wallbox.get_scenario_info("home", ["Type2", "Schuko", "ChaDeMo"])


def test_scenario_info_no_charging_points():
    ch = charger.Charger("charger", [])
    with pytest.raises(
        ValueError,
        match="Scenario dictionary requested of charger charger with no charging points",
    ):
        ch.get_scenario_info("0", ["Schuko"])
