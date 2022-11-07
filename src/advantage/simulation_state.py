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

        # charging_schedule = pd.DataFrame(columns=["start", "end", "vehicle", "location", "demand"])

    def remove_vehicle(self, vehicle: "Vehicle"):
        lists = [self.driving_vehicles, self.parking_vehicles, self.charging_vehicles]
        for current_list in lists:
            while vehicle in current_list:
                current_list.remove(vehicle)

    def update_vehicle(self, vehicle: "Vehicle"):
        self.remove_vehicle(vehicle)
        # TODO add enum for status
        if vehicle.status == "driving":
            self.driving_vehicles.append(vehicle)
        elif vehicle.status == "parking":
            self.parking_vehicles.append(vehicle)
        elif vehicle.status == "charging":
            self.charging_vehicles.append(vehicle)