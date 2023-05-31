from advantage.vehicle import Vehicle
from advantage.event import Status

import json


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

        self.events = {}  # TODO dict of timestamp > vehicle, based on task start time

        self.accumulated_results = {}

        # charging_schedule = pd.DataFrame(columns=["start", "end", "vehicle", "location", "demand"])

    def remove_vehicle(self, vehicle: "Vehicle"):
        lists = [self.driving_vehicles, self.parking_vehicles, self.charging_vehicles]
        for current_list in lists:
            while vehicle in current_list:
                current_list.remove(vehicle)

    def update_vehicle(self, vehicle: "Vehicle"):
        self.remove_vehicle(vehicle)
        if vehicle.status == Status.DRIVING:
            self.driving_vehicles.append(vehicle)
        elif vehicle.status == Status.PARKING:
            self.parking_vehicles.append(vehicle)
        elif vehicle.status == Status.CHARGING:
            self.charging_vehicles.append(vehicle)

    def log_data(self, charging_demand, charging_result, distance, consumption):
        """Accumulates specified event data and save it in self.accumulated_results."""
        self.add_to_accumulated_results("distance", distance)
        self.add_to_accumulated_results("charging_demand", charging_demand)
        self.add_to_accumulated_results("consumption", consumption)
        if charging_result is not None:
            cost = charging_result["cost"]
            emission = charging_result["emission"]
            energy_from_feed_in = charging_demand * charging_result["feed_in"]
            energy_from_grid = charging_demand - energy_from_feed_in
            self.add_to_accumulated_results("cost", cost)
            self.add_to_accumulated_results("emission", emission)
            self.add_to_accumulated_results("energy_from_feed_in", energy_from_feed_in)
            self.add_to_accumulated_results("energy_from_grid", energy_from_grid)
            self.add_to_accumulated_results(
                "actual_energy_from_grid", charging_result["grid_energy"]
            )

    def calculate_key_log_parameters(self):
        """Calculates values for the log files."""
        try:
            if self.accumulated_results["charging_demand"]:
                self_sufficiency = min(
                    round(
                        self.accumulated_results["energy_from_feed_in"]
                        / self.accumulated_results["charging_demand"],
                        4,
                    ),
                    1,
                )
                self.accumulated_results["self_sufficiency"] = self_sufficiency
        except KeyError:
            pass

    def export_log(self, save_directory):
        """Exports accumulated data to a JSON file."""
        self.calculate_key_log_parameters()
        if not save_directory.exists():
            save_directory.mkdir(parents=True, exist_ok=True)

        file_path = save_directory / "accumulated_results.json"

        with open(file_path, "w") as f:
            json.dump(self.accumulated_results, f, indent=4)

    def add_to_accumulated_results(self, key, value):
        """Adds a value to the accumulated data."""
        if key not in self.accumulated_results:
            self.accumulated_results[key] = value
        else:
            self.accumulated_results[key] = round(
                self.accumulated_results[key] + value, 4
            )
