from importlib import import_module
from typing import TYPE_CHECKING
import pandas as pd

from advantage.util.conversions import step_to_timestamp
from advantage.event import Status
from advantage.spiceev_interface import get_charging_characteristic

if TYPE_CHECKING:
    from advantage.simulation import Simulation
    from advantage.vehicle import Vehicle
    from advantage.event import Task


def class_from_str(strategy_name: str):
    """Returns a constructor from the specified strategy."""
    import_name = strategy_name.lower()
    class_name = "".join([s.capitalize() for s in strategy_name.split("_")])
    module = import_module("advantage.simulation_types." + import_name)
    return getattr(module, class_name)


class SimulationType:
    def __init__(self, simulation: "Simulation"):
        """SimulationType base constructor.

        Parameters
        ----------
        simulation : Simulation
            The current simulation object
        """
        self.simulation = simulation

    def execute_task(self, vehicle: "Vehicle", task: "Task"):
        """Makes a vehicle execute a specified task.

        Parameters
        ----------
        vehicle : Vehicle
            Vehicle object executing the task
        task : Task
            Task to be executed
        """
        if task.task == Status.DRIVING:
            if not task.is_calculated:
                trip = self.simulation.driving_sim.calculate_trip(
                    task.start_point,
                    task.end_point,
                    vehicle.vehicle_type,
                    self.simulation.average_speed,
                    self.simulation.time_series[task.start_time],
                )
                task.delta_soc = trip["soc_delta"]
                task.float_time = trip["trip_time"]
            distance, _ = self.simulation.driving_sim.get_location_values(
                task.start_point, task.end_point
            )
            vehicle.drive(
                step_to_timestamp(self.simulation.time_series, task.start_time),
                task.start_time,
                task.end_time - task.start_time,
                task.end_point,
                vehicle.soc + task.delta_soc,
                distance,
                self.simulation.observer,
            )
        elif task.task == Status.CHARGING:
            # call spiceev to calculate charging
            spiceev_scenario = self.simulation.call_spiceev(
                task.start_point,
                task.start_time,
                task.end_time,
                vehicle,
            )
            # charged_soc = spiceev_scenario.socs[-1][0] - vehicle.soc
            # print(task.delta_soc, charged_soc, vehicle.soc)
            # TODO fix issue with expected delta_soc and actual charged
            # soc being off when actual starting soc is higher
            charging_result = get_charging_characteristic(
                spiceev_scenario,
                self.simulation.feed_in_cost,
                self.simulation.emission,
                self.simulation.emission_options,
            )
            nominal_charging_power = list(
                spiceev_scenario.components.charging_stations.values()
            )[0].max_power
            # report = aggregate_local_results(spiceev_scenario, "GC1")

            # calculate average charging power
            charging_power_list = [
                list(d.values())[0] for d in spiceev_scenario.connChargeByTS["GC1"]
            ]
            average_charging_power = sum(charging_power_list) / len(charging_power_list)
            # execute charging event
            vehicle.charge(
                step_to_timestamp(self.simulation.time_series, task.start_time),
                task.start_time,
                task.end_time - task.start_time,
                average_charging_power,
                spiceev_scenario.socs[-1][0],
                nominal_charging_power,
                charging_result,
                self.simulation.observer,
            )
            vehicle.current_location.update_output(
                step,
                # step_to_timestamp(self.simulation.time_series, step),
                task.end_time - task.start_time,
                round(mean(spiceev_scenario.totalLoad["GC1"]), 4),
                self.simulation.time_steps,
                # self.simulation.time_series,
                self.simulation.step_size,
                self.simulation.save_directory,
            )


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
        consumption = 0.0
        consumption_list = [(start, start, vehicle.soc)]
        for _, task in sorted(vehicle.tasks.items()):
            if start < task.end_time < end:
                if task.task == Status.DRIVING:
                    consumption += task.delta_soc
                    consumption_list.append(
                        (task.start_time, task.end_time, vehicle.soc + consumption)
                    )
                if task.task == Status.CHARGING:
                    # TODO check how much this would charge, relevant for ondemand
                    pass
        return pd.DataFrame(
            consumption_list, columns=["drive_start", "timestep", "soc"]
        )
