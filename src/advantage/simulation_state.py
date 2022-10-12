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
        self.driving_vehicles = []  # is busy with a job
        self.parking_vehicles = []  # is ready for the next job
        self.charging_vehicles = []  # vehicle is charging

    def remove_vehicle(self, vehicle: "Vehicle"):           # eventuell dict mit {key, value}
        if vehicle in (self.driving_vehicles or self.parking_vehicles or self.charging_vehicles):
            self.driving_vehicles.remove(vehicle)
            self.parking_vehicles.remove(vehicle)
            self.charging_vehicles.remove(vehicle)

    def update_vehicle(self, vehicle: "Vehicle"):
        self.remove_vehicle(vehicle)
        if vehicle.status == "driving" and vehicle not in self.driving_vehicles:
            self.driving_vehicles.append(vehicle)
        elif vehicle.status == "parking" and vehicle not in self.parking_vehicles:
            self.parking_vehicles.append(vehicle)
        elif vehicle.status == "charging" and vehicle not in self.charging_vehicles:
            self.charging_vehicles.append(vehicle)


charging_schedule = pd.DataFrame(columns=["start", "end", "vehicle", "location", "demand"])
