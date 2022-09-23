import pandas as pd
from advantage.vehicle import Vehicle


class SimulationState:
    """
    Provides the current state of the simulation:
    - schedule (from Scenario)
    - state of all vehicles
        - active (active trip) / inactive (returning from job, parking, charging)
        - state of all locations incl. chargers
    - creates charging_schedule (DF: start, end, vehicle, location, energy_demand)
    _________________________________________________________________________________
    fleet management distributes tasks to vehicles
    - update each timestep
    """

    def __init__(self, locations):
        self.active_vehicles = {'busy': []}
        self.inactive_vehicles = {
            'parking': [],  # has no job in the pipeline
            'charging': []}  # is charging and has a following job

# Wie viele states soll es geben? (parken, fahren...)

    def update_vehicle(self, vehicle: "Vehicle"):
        active_vehicles = {'busy': []}
        inactive_vehicles = {
            'parking': [],  # has no job in the pipeline
            'charging': [],  # is charging and has a following job
            'end_trip': []}  # is ending its last job

        if vehicle.status == "parking":
            inactive_vehicles["parking"].append(vehicle.vehicle_type)
        elif vehicle.status == "charging":
            inactive_vehicles["charging"].append(vehicle.vehicle_type)
        elif vehicle.status == "end_trip":
            inactive_vehicles["end_trip"].append(vehicle.vehicle_type)
        else:
            active_vehicles["busy"].append(vehicle.vehicle_type)

        state_locations = {
            "name": [vehicle.name],
            "rotation": [vehicle.rotation],
            "current_location": [vehicle.current_location],
        }


charging_schedule = pd.DataFrame(columns=["start", "end", "vehicle", "location", "demand"])
