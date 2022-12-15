from advantage.ride import RideCalc
import pandas as pd
import pytest
import pathlib


@pytest.fixture()
def driving_sim():
    cons_path = pathlib.Path("scenarios", "public_transport_base", "consumption.csv")
    cons = pd.read_csv(cons_path)
    return RideCalc(cons, cons, cons)  # TODO add inclines/distances


def test_get_consumption(driving_sim):
    # TODO change for new consumption table
    error_list = []
    if not 49.706 == driving_sim.get_consumption("bus_18m", -0.04, -10, 2.626, 0.):
        error_list.append("First result is wrong")
    if not 1.163 == driving_sim.get_consumption("atlas_7m", 0.04, 20, 37.093, 0.9):
        error_list.append("Second result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.04, -12.5, 2.626, 0.)
    if not 62.502 > consumption > 49.706:
        error_list.append("Third result is wrong")
    consumption = driving_sim.get_consumption("bus_18m", -0.03, 0., 2.626, 0.)
    if not 28.303 > consumption > 28.154:
        error_list.append("Fourth result is wrong")

    assert not error_list,  "errors occured:\n{}".format("\n".join(error_list))
