from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advantage.simulation import Simulation
    from advantage.vehicle import Vehicle


def class_from_str(strategy_name):
    import_name = strategy_name.lower()
    class_name = "".join([s.capitalize() for s in strategy_name.split("_")])
    module = import_module("advantage.simulation_types." + import_name)
    return getattr(module, class_name)


class SimulationType:
    """ """

    def __init__(self, simulation: "Simulation"):
        self.simulation = simulation

    def get_predicted_soc(self, vehicle: "Vehicle", start: int, end: int):
        consumption = 0
        for task in vehicle.tasks:
            if start < task.arrival_time < end:
                if task.task == "driving":
                    # TODO run task through driving simulation, add result to consumption
                    trip = self.simulation.driving_sim.calculate_trip(
                        task.departure_point,
                        task.arrival_point,
                        vehicle.vehicle_type,
                        20.0,
                    )
                    print(consumption)
                    consumption += trip["soc_delta"]
                if task.task == "charging":
                    # TODO check how much this would charge
                    pass
        return vehicle.soc - consumption
