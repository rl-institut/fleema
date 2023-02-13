from advantage.ride import RideCalc
import pandas as pd
import pytest
import pathlib


@pytest.fixture()
def driving_sim():
    cons_path = pathlib.Path("scenario_data", "bad_birnbach", "consumption.csv")
    cons = pd.read_csv(cons_path)
    temp_path = pathlib.Path("scenario_data", "bad_birnbach", "temperature.csv")
    temp = pd.read_csv(temp_path)
    return RideCalc(cons, cons, cons, temp)  # TODO add inclines/distances


def test_get_consumption(driving_sim):
    # TODO change for new consumption table
    """error_list = []
    if not -49.706 == driving_sim.get_consumption("bus_18m", -0.04, -10, 2.626, 0.0):
        error_list.append("First result is wrong")
    if not -1.163 == driving_sim.get_consumption("atlas_7m", 0.04, 20, 37.093, 0.9):
        error_list.append("Second result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.04, -12.5, 2.626, 0.0)
    if not -62.502 < consumption < -49.706:
        error_list.append("Third result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.03, 0.0, 2.626, 0.0)
    if not -28.303 < consumption < -28.154:
        error_list.append("Fourth result is wrong")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))"""


def test_get_temperature(driving_sim):
    # basic cases
    assert driving_sim.get_temperature("2022-01-01 01:01:00") == 12.9
    assert driving_sim.get_temperature("2022-01-01 02:01:00") == 12.2
    assert driving_sim.get_temperature("2022-01-01 03:01:00") == 12.1
    assert driving_sim.get_temperature("2022-01-01 04:01:00") == 12.0
    assert driving_sim.get_temperature("1999-01-01 00:01:00", option="lowest") == 2.4
    assert driving_sim.get_temperature("2022-01-01 23:01:00", option="lowest") == 2.9
    assert driving_sim.get_temperature("2022-01-01 22:01:00", option="lowest") == 3.2
    assert driving_sim.get_temperature("2022-01-01 21:01:00", option="lowest") == 3.4
    assert driving_sim.get_temperature("2022-01-01 13:30:00", option="highest") == 24.2
    assert driving_sim.get_temperature("2022-01-01 14:59:00", option="highest") == 24.2
    assert driving_sim.get_temperature("2022-01-01 15:00:00", option="highest") == 24.2
    assert driving_sim.get_temperature("2022-01-01 16:30:00", option="highest") == 24.2

    # bad option parameter
    assert driving_sim.get_temperature("2022-01-01 16:30:00", option="bad option") == 20.2
    assert driving_sim.get_temperature("2022-01-01 00:30:00", option="bad option") == 13.3

    # wrong datetime string format
    assert driving_sim.get_temperature("2022-01-01T16:30:00") == 13.3
    assert driving_sim.get_temperature("2022-01-01T16:30:00", option="lowest") == 2.4
    assert driving_sim.get_temperature("2022-01-01T16:30:00", option="highest") == 24.1
    assert driving_sim.get_temperature("2022-01-01T16:30:00", option="bad option") == 13.3
