import datetime
import pathlib
from spice_ev.scenario import Scenario

from advantage.util.helpers import deep_update


def get_spice_ev_scenario_dict(
    vehicle, location, point_id, timestamp: datetime.datetime, time, cost_options
):
    """This function creates a dictionary for SpiceEV.

    Parameters
    ----------
    vehicle : Vehicle
        Given Vehicle object for this SpiceEV scenario.
    location : Location
        Used location.
    point_id : int
        ID of the ChargingPoint.
    timestamp : str
        Timestamp that marks the starting time.
    time : int
        Number of time intervals.

    Returns
    -------
    dict
        Nested SpiceEV dictionary.

    """
    scenario_dict = {
        "scenario": {
            "start_time": timestamp.isoformat(),
            "interval": 1,
            "n_intervals": time,
            "discharge_limit": 0.5,
        },
        "components": {},
        "events": {
            "grid_operator_signals": {},
            "external_load": {},
            "energy_feed_in": {},
            "energy_price_from_csv": {
                "csv_file": cost_options["csv_path"],
                "start_time": cost_options["start_time"],
                "step_duration_s": cost_options["step_duration"],
                "grid_connector_id": "GC1",
                "column": cost_options["column"],
            },
            "vehicle_events": {},
        },
    }
    # TODO photovoltaics is only relevant for Einspeisevergütung
    spice_ev_dict = dict(scenario_dict, **vehicle.scenario_info)
    deep_update(
        spice_ev_dict, location.get_scenario_info(vehicle.vehicle_type.plugs, point_id)
    )
    departure_time = timestamp + datetime.timedelta(minutes=time)
    spice_ev_dict["components"]["vehicles"][vehicle.id][
        "estimated_time_of_departure"
    ] = departure_time.isoformat()

    return spice_ev_dict


def run_spice_ev(spice_ev_dict, strategy) -> "Scenario":
    """This function runs the scenario and returns it.

    Parameters
    ----------
    spice_ev_dict : dict
        Nested SpiceEV dictionary that holds all relevant information for the scenario.
    strategy : str
        Name of the strategy.

    Returns
    -------
    Scenario
        Scenario object.

    """
    scenario = Scenario(spice_ev_dict)
    scenario.run(strategy, {"testing": True})
    return scenario


# TODO add function that takes a task (if task == driving) and runs spiceev with it


def get_charging_characteristic(scenario, feed_in_cost):
    """Calculate average cost and part of charging from feed-in in a spice_ev scenario.

    Parameters
    ----------
    scenario : Scenario
        SpiceEV Scenario object.
    feed_in_cost : float
        Cost of feed in energy in €/kWh

    Returns
    -------
    dict[string, float]
        Keys: "cost" contains average cost in €/kWh, "feed_in": renewable part of charging energy [0-1]

    """
    total_cost = 0
    total_charge = 0
    total_charge_from_feed_in = 0
    for i in range(scenario.n_intervals):
        charge = list(scenario.connChargeByTS["GC1"][i].values())[0]
        feed_in = scenario.feedInPower["GC1"][i]
        cost = scenario.prices["GC1"][i]

        total_charge += charge
        total_charge_from_feed_in += min(charge, feed_in)

        total_cost += max(charge - feed_in, 0) * cost + feed_in * feed_in_cost

    average_cost = total_cost / total_charge

    feed_in_factor = min(total_charge_from_feed_in / total_charge, 1)
    result_dict = {
        "cost": round(average_cost, 4),
        "feed_in": round(feed_in_factor, 4),
    }
    return result_dict
