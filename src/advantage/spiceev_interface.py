import datetime
from src.scenario import Scenario

from advantage.util.helpers import deep_update


def get_spice_ev_scenario_dict(vehicle, location, point_id, timestamp, time):
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
        "constants": {},
        "events": {
            "grid_operator_signals": {},
            "external_load": {},
            "energy_feed_in": {},
            "vehicle_events": {},
        },
    }
    spice_ev_dict = dict(scenario_dict, **vehicle.scenario_info)
    deep_update(
        spice_ev_dict, location.get_scenario_info(vehicle.vehicle_type.plugs, point_id)
    )
    departure_time = timestamp + datetime.timedelta(minutes=time)
    spice_ev_dict["constants"]["vehicles"][vehicle.id][
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
    scenario.run(strategy, {})
    return scenario


# TODO add function that takes a task (if task == driving) and runs spiceev with it
