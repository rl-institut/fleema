import advantage.vehicle as vehicle
import advantage.location as location
import advantage.charger as charger
from advantage.util.conversions import step_to_timestamp
from advantage.spiceev_interface import (
    get_spice_ev_scenario_dict,
    run_spice_ev,
)

import pytest
import datetime
import pandas as pd


@pytest.fixture()
def car():
    car_type = vehicle.VehicleType(
        battery_capacity=30,
        base_consumption=0.2,
        charging_capacity={"Type2": 22},
        charging_curve=[[0, 11], [0.8, 11], [1, 11]],
    )
    car = vehicle.Vehicle("car", vehicle_type=car_type, soc=0.5)
    return car


@pytest.fixture()
def spot():
    # TODO input actual values for Charger
    charge_spot = charger.Charger.from_json(
        "point", 1, [charger.PlugType("Type2_22", 22, "Type2")]
    )
    spot = location.Location(chargers=[charge_spot], grid_info={"power": 150})
    return spot


@pytest.fixture()
def time_series():
    time_series = pd.date_range(
        datetime.datetime(2022, 1, 1),
        datetime.datetime(2022, 1, 3),
        freq="min",
        inclusive="left",
    )
    return time_series


@pytest.fixture()
def cost_options(time_series):
    cost_options = {
        "csv_path": "scenario_data/bad_birnbach/cost.csv",
        "start_time": step_to_timestamp(time_series, 0).isoformat(),
        "step_duration": 3600,
        "column": "cost",
    }
    return cost_options


def test_create_dict(car, time_series, spot, cost_options):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    spice_dict = get_spice_ev_scenario_dict(car, spot, "point_0", time_stamp, 10, cost_options)
    error_list = []
    if "vehicles" not in spice_dict["components"].keys():
        error_list.append("Vehicles is not in components.")
    if "vehicle_types" not in spice_dict["components"].keys():
        error_list.append("Vehicle_types is not in components.")

    assert not error_list, "errors occured:\n{}".format("\n".join(error_list))


def test_run_spice_ev(car, time_series, spot, cost_options):
    start_step = 5
    time_stamp = step_to_timestamp(time_series, start_step)
    spice_dict = get_spice_ev_scenario_dict(car, spot, "point_0", time_stamp, 10, cost_options)
    spice_dict["components"]["vehicles"]["car"]["connected_charging_station"] = "point_0"
    scenario = run_spice_ev(spice_dict, "balanced")
    # check if soc is higher than before
    assert scenario.strat.world_state.vehicles[car.id].battery.soc > car.soc  # type: ignore


def test_get_charging_characteristic_emission():
    pass
