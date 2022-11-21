from advantage.ride import RideCalc
import pandas as pd

import pytest


def test_get_consumption():
    import pathlib
    cons_path = pathlib.Path("..", "scenarios", "public_transport_base", "consumption.csv")
    cons = pd.read_csv(cons_path)
    rc = RideCalc(cons, cons, cons)

    assert 49.706 == rc.get_consumption("bus_18m", -0.04, -10, 2.626, 0.)
    assert 1.163 == rc.get_consumption("atlas_7m", 0.04, 20, 37.093, 0.9)

    consumption = rc.get_consumption("bus_18m", -0.04, -12.5, 2.626, 0.)
    assert 62.502 > consumption > 49.706

    consumption = rc.get_consumption("bus_18m", -0.03, 0., 2.626, 0.)
    assert 28.303 > consumption > 28.154
