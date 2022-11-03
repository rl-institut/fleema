import datetime
from src.scenario import Scenario

from advantage.util.helpers import deep_update


def get_spice_ev_scenario_dict(vehicle, location, point_id, timestamp, time):
    scenario_dict = {
        "scenario": {
            "start_time": timestamp.isoformat(),
            "interval": 1,
            "n_intervals": time,
            "discharge_limit": 0.5
        },
        "constants": {},
        "events": {
            "grid_operator_signals": {},
            "external_load": {},
            "energy_feed_in": {},
            "vehicle_events": {}
        }
    }
    spice_ev_dict = dict(scenario_dict, **vehicle.scenario_info)
    deep_update(spice_ev_dict, location.get_scenario_info(point_id, vehicle.vehicle_type.plugs))
    departure_time = timestamp + datetime.timedelta(minutes=time)
    spice_ev_dict["constants"]["vehicles"][f"{vehicle.vehicle_type.name}_0"]["estimated_time_of_departure"] = \
        departure_time.isoformat()

    return spice_ev_dict


def run_spice_ev(spice_ev_dict, strategy) -> "Scenario":
    scenario = Scenario(spice_ev_dict)
    scenario.run(strategy, {})
    return scenario

# TODO add function that takes a task (if task == driving) and runs spiceev with it
