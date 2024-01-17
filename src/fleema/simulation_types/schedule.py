import pandas as pd
import pathlib

from fleema.simulation_type import SimulationType
from fleema.plot import plot
from fleema.util.helpers import get_next_index
from typing import TYPE_CHECKING
from operator import itemgetter

if TYPE_CHECKING:
    from fleema.simulation import Simulation
    from fleema.vehicle import Vehicle


class Schedule(SimulationType):
    def __init__(self, simulation: "Simulation"):
        super().__init__(simulation)

    def _create_initial_schedule(self):
        """Creates vehicles and tasks from the scenario schedule."""
        self.simulation.vehicles_from_schedule()
        # get tasks for every row of the schedule
        self.simulation.schedule.apply(self.simulation.task_from_schedule, axis=1)  # type: ignore

    def get_charging_slots(self, break_list, soc_df, vehicle):
        """Calculate charging slots for a vehicle.

        Parameters
        ----------
        break_list : List[Task]
            Result from vehicle.get_breaks()
        soc_df : DataFrame
            Result from self.get_predicted_soc()
        vehicle : Vehicle

        Returns
        -------
        list
            Returns a sorted list containing results from the evaluate charging station function.
            Better results are at the top
        """
        # initialize variables
        charging_list = [{}] * len(break_list)
        lowest_current_soc = vehicle.soc_start
        for counter, task in enumerate(break_list):
            # for all locations with chargers, evaluate the best option. save task, best location, evaluation
            charging_list_temp = []
            for loc in self.simulation.charging_locations:
                soc_df_slice = soc_df.loc[soc_df["timestep"] >= task.start_time]
                if len(soc_df_slice.index):
                    # get lowest possible soc at this point in time (if no charging has happened)
                    lowest_current_soc = max(
                        soc_df_slice.iat[0, -1], self.simulation.soc_min
                    )
                charging_list_temp.append(
                    self.simulation.evaluate_charging_location(
                        vehicle.vehicle_type,
                        loc,
                        task.start_point,
                        task.end_point,
                        task.start_time,
                        task.end_time,
                        lowest_current_soc,
                    )
                )
            # compare locations and choose the best one
            # TODO change sorting depending on config? score is always most important,
            # after could come cost, charge, consumption...
            charging_list_temp.sort(key=itemgetter("consumption"))
            charging_list_temp.sort(
                key=itemgetter("score", "delta_soc", "charge"), reverse=True
            )
            charging_list[counter] = charging_list_temp[0]
        charging_list.sort(key=itemgetter("score", "delta_soc", "charge"), reverse=True)
        return charging_list

    def _distribute_charging_slots(self, start: int, end: int, end_soc: float):
        """Choose charging slots in the specified timeframe and add them to the vehicle.

        Parameters
        ----------
        start : int
            Starting timestep
        end : int
            Ending timestep
        end_soc : float
            desired end SoC
        """
        # go through all vehicles, check SoC after all tasks (end of day). continues if <20%
        # evaluate charging slots
        # distribute slots by highest total score (?)
        # for conflicts, check amount of charging spots at location and total possible power
        vehicles = list(self.simulation.vehicles.values())
        index = 0
        # rerun the loop until valid schedule has been created
        print(f"==== Distributing charging slots ====")
        while vehicles:
            veh = vehicles[index]
            chosen_event = self._find_next_charging_slot(start, end, veh, end_soc)
            if chosen_event is None:
                del vehicles[index]
                index = get_next_index(index, len(vehicles))
                continue
            self._add_chosen_event(veh, chosen_event)
            self.simulation.observer.add_vehicle_event(chosen_event["charge_event"])
            index = get_next_index(index, len(vehicles))

    def _find_next_charging_slot(
        self, start: int, end: int, vehicle: "Vehicle", end_soc: float
    ):
        """Tries to find the next best charging slot for a vehicle.

        Parameters
        ----------
        start : int
            Starting timestep
        end : int
            Ending timestep
        vehicle : Vehicle
            Vehicle to find charging slots for

        Returns
        -------
        Optional[list]
            contains charging event options, format same as in self.get_charging_slots
        """
        # initialize variables
        soc_df = self.get_predicted_soc(vehicle, start, end)
        break_list = vehicle.get_breaks(start, end)
        if vehicle.charging_list is None:
            charging_list = self.get_charging_slots(break_list, soc_df, vehicle)
            vehicle.set_charging_list(charging_list)

        last_soc = soc_df.iat[-1, -1]
        # check if vehicle falls under minimum soc
        min_charge = max(self.simulation.soc_min - last_soc, 0)
        end_of_day_charge = max(end_soc - last_soc, 0)
        if not min_charge and not end_of_day_charge:
            return None

        soc_df_slice = soc_df.loc[soc_df["soc"] <= self.simulation.soc_min].copy()
        soc_df_slice["necessary_charging"] = (
            self.simulation.soc_min - soc_df_slice["soc"]
        )
        last_index = soc_df.index[-1]
        if last_index not in soc_df_slice.index:
            last_row = soc_df.loc[last_index, :].copy()
            last_row["necessary_charging"] = self.simulation.soc_min - last_row["soc"]
            soc_df_slice.loc[last_index] = last_row
        
        min_soc_bool = soc_df_slice["necessary_charging"] <= 0
        min_soc_satisfied = min_soc_bool.all()
        end_soc_satisfied = (
            soc_df_slice.iat[-1, -1] < self.simulation.soc_min - end_soc
        )
        if (
            min_soc_satisfied
            and end_soc_satisfied
        ):
            return None
        
        # iterate through a sorted list of charging options, best options first
        while True:
            if vehicle.charging_list:
                charge_option = vehicle.charging_list.pop(0)
            else:
                return None
            # only use options with a score higher than 0. TODO set higher minimum score in config?
            if charge_option["score"] > 0:
                # if capacity of charger is already blocked, don't add this charging event
                # currently charging events are calculated separately, so we have to prevent multi charging here
                if not charge_option["charge_event"].start_point.is_available(
                    charge_option["charge_event"].start_time,
                    charge_option["charge_event"].end_time,
                ):
                    continue
                # if not min_soc_satisfied:
                charge_index = soc_df_slice.loc[
                    soc_df_slice["timestep"] >= charge_option["timestep"]
                ].index

                # apply delta soc to timeseries
                delta_soc = charge_option["delta_soc"]
                for i in charge_index:
                    new_soc = min(soc_df_slice.at[i, "soc"] + delta_soc, 1.0)
                    if new_soc == 1.0:
                        delta_soc = new_soc - soc_df_slice.at[i, "soc"]
                    soc_df_slice.at[i, "soc"] = new_soc
                    soc_df_slice.at[i, "necessary_charging"] -= delta_soc

                return charge_option

            else:
                if min_soc_satisfied:
                    if not end_soc_satisfied:
                        print(
                            f"Desired SoC {end_soc} for the last time step couldn't be met for vehicle {vehicle.id}"
                        )
                    return charge_option

                # TODO rename to allow_negative_soc
                if not self.simulation.delete_rides:
                    raise ValueError(
                        f"Not enough charging possible for vehicle {vehicle.id}!"
                    )
                else:
                    # TODO remove delete_ride function
                    # self.delete_ride(soc_df_slice, vehicle)
                    print(
                            f"SoC requirements for vehicle {vehicle.id} couldn't be met"
                        )
                    return None

    def delete_ride(self, soc_df, vehicle):
        # get all tasks that still need charging to be possible
        impossible_tasks = soc_df.loc[soc_df["necessary_charging"] > 0]
        # get starting time of first impossible task (row 0, column 0: "timestep")
        first_impossible_task_start = impossible_tasks.iat[0, 0]
        # cancel the impossible task. not setting the valid_schedule flag results in
        # a recalculation of charging slots without the impossible task
        first_impossible_task = vehicle.get_task(first_impossible_task_start)
        if first_impossible_task is None:
            raise ValueError("No task to remove or change to has been found")
        vehicle.remove_task(first_impossible_task)

        next_task = vehicle.get_next_task(int(first_impossible_task_start))
        if next_task is not None:
            vehicle.remove_task(next_task)
            next_task.start_point = first_impossible_task.start_point
            next_task.is_calulated = False
            vehicle.add_task(next_task)
            # TODO change time needed for this task?

        print(
            f"Not enough charging possible for vehicle {vehicle.id},",
            f"ride starting at timestep {first_impossible_task_start} had to be removed!",
        )
        self.simulation.observer.add_to_accumulated_results(
            f"deleted_rides_vehicle_{vehicle.id}", 1
        )

    def _add_chosen_event(self, vehicle, charge_option):
        vehicle.add_task(charge_option["charge_event"])
        if "task_to" in charge_option:
            vehicle.add_task(charge_option["task_to"])
        if "task_from" in charge_option:
            vehicle.add_task(charge_option["task_from"])

    def run(self):
        """Run the scenario with this strategy."""
        # create tasks for all vehicles from input schedule
        self._create_initial_schedule()
        # create charging tasks based on rating
        end_of_day_soc = self.simulation.end_of_day_soc
        self._distribute_charging_slots(0, self.simulation.time_steps, end_of_day_soc)
        # create save directory
        if True in self.simulation.outputs.values():
            self.simulation.save_directory.mkdir(parents=True, exist_ok=True)
            self.save_inputs()

        # simulate fleet step by step
        for step in range(self.simulation.time_steps):
            # check all vehicles for tasks
            for veh in self.simulation.vehicles.values():
                task = veh.get_task(step)
                if task is None:
                    continue
                else:
                    self.execute_task(veh, task)

                veh.export(self.simulation.save_directory)
        if self.simulation.outputs["vehicle_csv"]:
            self.simulation.observer.export_log(self.simulation.save_directory)

        # generate power grid timeseries for locations
        if self.simulation.outputs["location_csv"]:
            output = {
                "timestamp": self.simulation.time_series,
                "total_power": [0 for _ in range(self.simulation.time_steps)],
                "total_connected_vehicles": [
                    0 for _ in range(self.simulation.time_steps)
                ],
            }

            for location in self.simulation.charging_locations:
                if location.output is None:
                    continue
                for k, v in location.output.items():
                    if "total_power" in k:
                        output["total_power"] = [
                            sum(x) for x in zip(v, output["total_power"])
                        ]
                    if "total_connected_vehicles" in k:
                        output["total_connected_vehicles"] = [
                            sum(x) for x in zip(v, output["total_connected_vehicles"])
                        ]
                    output[k] = v

            df = pd.DataFrame(output)
            df.to_csv(
                pathlib.Path(
                    self.simulation.save_directory, "power_grid_timeseries.csv"
                )
            )
            self.simulation.outputs["total_power"] = output["total_power"]

        plot(self.simulation)
