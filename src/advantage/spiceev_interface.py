import datetime


def get_spice_ev_scenario_dict(vehicle, location, timestamp, time):
    scenario_dict = {
        "scenario": {
            "start_time": "2018-01-01T01:00:00+02:00",
            "interval": 15,
            "n_intervals": 2880,
            "discharge_limit": 0.5
        },
        "constants": {}
    }
    spice_ev_dict = dict(scenario_dict, **vehicle.scenario_info)
    # spice_ev_dict.update(location.scenario_info)  # TODO implement
    spice_ev_dict["constants"]["vehicles"][f"{vehicle.vehicle_type.name}_0"]["estimated_time_of_departure"] = \
        str(timestamp + datetime.timedelta(minutes=time))

    return spice_ev_dict
