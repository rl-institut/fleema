from importlib import import_module
from typing import TYPE_CHECKING
import pandas as pd

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
        """Calculates predicted SoC of given vehicle after the given timespan by running all tasks.

        Parameters
        ----------
        vehicle : Vehicle
            Vehicle object to predict SoC for
        start : int
            Starting time step of the relevant time window
        end : int
            Ending time step of the relevant time window

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns "timestep" and "soc", containing predicted soc at specified times
        """
        consumption = 0
        consumption_list = []
        for task in vehicle.tasks:
            if start < task.arrival_time < end:
                if task.task == "driving":
                    trip = self.simulation.driving_sim.calculate_trip(
                        task.departure_point,
                        task.arrival_point,
                        vehicle.vehicle_type,
                        20.0,
                    )
                    print(consumption)  # TODO remove
                    consumption += trip["soc_delta"]
                    consumption_list.append((task.arrival_time, vehicle.soc - consumption))
                if task.task == "charging":
                    # TODO check how much this would charge
                    pass
        return pd.DataFrame(consumption_list, columns =["timestep", "soc"])