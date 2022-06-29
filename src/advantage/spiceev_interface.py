import datetime


def get_spice_ev_scenario_dict(vehicle, location, timestamp, time):
    scenario_dict = {
        "scenario": {
            "start_time": timestamp.isoformat(),
            "interval": 1,
            "n_intervals": time,
            "discharge_limit": 0.5
        },
        "constants": {}
    }
    spice_ev_dict = dict(scenario_dict, **vehicle.scenario_info)
    # spice_ev_dict.update(location.scenario_info)  # TODO implement
    departure_time = timestamp + datetime.timedelta(minutes=time)
    spice_ev_dict["constants"]["vehicles"][f"{vehicle.vehicle_type.name}_0"]["estimated_time_of_departure"] = \
        departure_time.isoformat()

    return spice_ev_dict
