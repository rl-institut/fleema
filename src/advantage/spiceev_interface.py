import datetime
import warnings
import math
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


def run_spice_ev(spice_ev_dict, strategy, ignore_warnings=True) -> "Scenario":
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
    if ignore_warnings:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            scenario.run(strategy, {})
    else:
        scenario.run(strategy, {})
    return scenario


def get_charging_characteristic(
    scenario, feed_in_cost, emission_df=None, emission_options=None
):
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
        Keys: "cost" contains average cost in €/kWh,
        "feed_in": renewable part of charging energy [0-1],
        "emission": total CO2-emission in g

    """
    total_cost = 0
    total_charge = 0
    total_charge_from_feed_in = 0
    total_emission = 0
    timestamp = scenario.start_time
    spice_ev_timestep = int(60 / scenario.stepsPerHour)  # length of one spice_ev timestep in minutes
    for i in range(scenario.n_intervals):
        charge = list(scenario.connChargeByTS["GC1"][i].values())[0]
        feed_in = scenario.feedInPower["GC1"][i]
        cost = scenario.prices["GC1"][i]

        total_charge += charge
        total_charge_from_feed_in += min(charge, feed_in)

        total_cost += max(charge - feed_in, 0) * cost + feed_in * feed_in_cost

        if emission_df is not None:
            current_emission = get_current_emission(
                timestamp, emission_df, emission_options
            )
            total_emission += max(charge - feed_in, 0) * current_emission / scenario.stepsPerHour
        # set new timestamp
        timestamp += datetime.timedelta(minutes=spice_ev_timestep)

    average_cost = total_cost / total_charge

    feed_in_factor = min(total_charge_from_feed_in / total_charge, 1)
    result_dict = {
        "cost": round(average_cost, 4),
        "feed_in": round(feed_in_factor, 4),
        "emission": round(total_emission, 4),
    }
    return result_dict


def get_current_emission(
    timestamp: datetime.datetime, emission_df, emission_options: dict
):
    """
    Gets the current emission value for a given timestamp and set of emission options.

    Parameters
    ----------
    timestamp : datetime.datetime
        The timestamp to get the emission value for.
    emission_df : pandas.DataFrame
        A DataFrame containing the emission data.
    emission_options : dict
        A dictionary containing the emission options.
        Required keys:
        - "start_time" : datetime.datetime
            The start time of the emission data.
        - "step_duration" : int
            The duration of each emission step in seconds.
        - "column" : str
            The name of the column containing the emission data in `emission_df`.

    Returns
    -------
    np.float64
        The current emission value at the given timestamp.

    Raises
    ------
    KeyError
        If any of the required keys are missing from `emission_options`.
    IndexError
        If the timestep calculated based on the given timestamp is outside the range of `emission_df`.
    """
    time_delta = timestamp - emission_options["start_time"]
    timestep = math.floor(
        time_delta.total_seconds() / emission_options["step_duration"]
    )
    try:
        return emission_df[emission_options["column"]].iat[timestep]
    except KeyError as ke:
        raise KeyError(f"Missing required key in emission_options: {ke}")
    except IndexError:
        raise IndexError("Timestamp is outside the range of emission_df.")
