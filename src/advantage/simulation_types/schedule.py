from advantage.simulation_type import SimulationType
from typing import TYPE_CHECKING
from operator import itemgetter

if TYPE_CHECKING:
    from advantage.simulation import Simulation
    from advantage.vehicle import Vehicle


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
                    lowest_current_soc = max(soc_df_slice.iat[0, -1], self.simulation.soc_min)
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
        for veh in self.simulation.vehicles.values():
            # rerun the loop until valid schedule has been created
            # TODO check if this could ever be an infinite loop, in theory it should delete tasks until possible
            chosen_events = None
            counter = 1
            while chosen_events is None:
                print(
                    f"==== Finding charging slots for vehicle {veh.id}, iteration {counter} ===="
                )
                chosen_events = self._find_charging_slots(start, end, veh, end_soc)
                counter += 1
            print(f"==== Simulating vehicle {veh.id} ====")
            self._add_chosen_events(veh, chosen_events)

    def _find_charging_slots(
        self, start: int, end: int, vehicle: "Vehicle", end_soc: float
    ):
        """Tries to find working charging slots for a vehicle.

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
        charging_list = self.get_charging_slots(break_list, soc_df, vehicle)

        chosen_events = []
        total_charge = 0
        min_soc_satisfied = False
        end_soc_satisfied = False

        last_soc = soc_df.iat[-1, -1]
        max_charge = 1 - last_soc
        # check if vehicle falls under minimum soc
        min_charge = max(self.simulation.soc_min - last_soc, 0)
        end_of_day_charge = max(end_soc - last_soc, 0)
        if not min_charge and not end_of_day_charge:
            return []

        soc_df_slice = soc_df.loc[soc_df["soc"] <= self.simulation.soc_min].copy()
        soc_df_slice["necessary_charging"] = (
            self.simulation.soc_min - soc_df_slice["soc"]
        )
        last_index = soc_df.index[-1]
        if last_index not in soc_df_slice.index:
            last_row = soc_df.loc[last_index, :].copy()
            last_row["necessary_charging"] = self.simulation.soc_min - last_row["soc"]
            soc_df_slice.loc[last_index] = last_row

        # iterate through a sorted list of charging options, best options first
        for charge_option in charging_list:
            # only use options with a score higher than 0. TODO set higher minimum score in config?
            if charge_option["score"] > 0:
                # if not min_soc_satisfied:
                charge_index = soc_df_slice.loc[
                    soc_df_slice["timestep"] >= charge_option["timestep"]
                ].index

                # apply delta soc to timeseries
                delta_soc = charge_option["delta_soc"]
                for i in charge_index:
                    new_soc = min(
                        soc_df_slice.at[i, 'soc'] + delta_soc, 1.0)
                    soc_df_slice.at[i, 'soc'] = new_soc
                    if new_soc == 1.0:
                        delta_soc = new_soc - soc_df_slice.at[i, 'soc']
                    soc_df_slice.at[i, 'necessary_charging'] -= delta_soc

                min_soc_bool = soc_df_slice["necessary_charging"] <= 0
                min_soc_satisfied = min_soc_bool.all()
                total_charge += charge_option["delta_soc"]
                end_soc_satisfied = (
                    soc_df_slice.iat[-1, -1] < self.simulation.soc_min - end_soc
                )

                chosen_events.append(charge_option)
                # TODO implement not choosing events if max charge is satisfied
                # and they don't contribute to min_soc or end_soc

                if (
                    total_charge > max_charge
                    and min_soc_satisfied
                    and end_soc_satisfied
                ):
                    return chosen_events

            else:
                if min_soc_satisfied:
                    if not end_soc_satisfied:
                        print(
                            f"Desired SoC {end_soc} for the last time step couldn't be met for vehicle {vehicle.id}"
                        )
                    return chosen_events

                if not self.simulation.delete_rides:
                    raise ValueError(
                        f"Not enough charging possible for vehicle {vehicle.id}!"
                    )
                else:
                    self.delete_ride(soc_df_slice, vehicle)
                    return None

    def delete_ride(self, soc_df, vehicle):
        # get all tasks that still need charging to be possible
        impossible_tasks = soc_df.loc[
            soc_df["necessary_charging"] > 0
        ]
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
            vehicle.add_task(next_task)
            # TODO change time needed for this task?

        print(
            f"Not enough charging possible for vehicle {vehicle.id},",
            f"ride starting at timestep {first_impossible_task_start} had to be removed!",
        )
        self.simulation.observer.add_to_accumulated_results(f"deleted_rides_vehicle_{vehicle.id}", 1)

    def _add_chosen_events(self, vehicle, chosen_events):
        for charge_option in chosen_events:
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
