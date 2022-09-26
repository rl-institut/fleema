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

    def __init__(self):
        self.driving_vehicles = {'driving': []}  # is busy with a job
        self.parking_vehicles = {'parking': []}  # is ready for the next job
        self.charging_vehicles = {'charging': []}  # vehicle is charging

    def update_vehicle(self, vehicle: "Vehicle"):
        if vehicle.status == "driving":
            driving_vehicles["driving"].append(vehicle.vehicle_type)
        elif vehicle.status == "parking":
            parking_vehicles["parking"].append(vehicle.vehicle_type)
        elif vehicle.status == "charging":
            charging_vehicles["charging"].append(vehicle.vehicle_type)


charging_schedule = pd.DataFrame(columns=["start", "end", "vehicle", "location", "demand"])
