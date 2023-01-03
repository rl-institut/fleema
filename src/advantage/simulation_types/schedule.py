from advantage.simulation_type import SimulationType
from typing import TYPE_CHECKING
from operator import itemgetter

if TYPE_CHECKING:
    from advantage.simulation import Simulation


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
                    lowest_current_soc = soc_df_slice.iat[0, 1]
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
        return charging_list

    def _distribute_charging_slots(self, start, end):
        """Choose charging slots in the specified timeframe and add them to the vehicle.

        Parameters
        ----------
        start : int
            Starting timestep
        end : int
            Ending timestep
        """
        # go through all vehicles, check SoC after all tasks (end of day). continues if <20%
        # evaluate charging slots
        # distribute slots by highest total score (?)
        # for conflicts, check amount of charging spots at location and total possible power
        for veh in self.simulation.vehicles.values():
            soc_df = self.get_predicted_soc(veh, start, end)
            break_list = veh.get_breaks(start, end)
            charging_list = self.get_charging_slots(break_list, soc_df, veh)

            charging_list.sort(key=itemgetter("score"), reverse=True)
            chosen_events = []
            total_charge = 0
            min_soc_satisfied = False
            max_charge = 1 - soc_df.iat[-1, 1]
            # check if vehicle falls under minimum soc
            min_charge = max(self.simulation.soc_min - soc_df.iat[-1, 1], 0)
            if min_charge:
                soc_df_slice = soc_df.loc[
                    soc_df["soc"] <= self.simulation.soc_min
                ].copy()
                soc_df_slice["necessary_charging"] = (
                    self.simulation.soc_min - soc_df_slice["soc"]
                )

                for charge_option in charging_list:
                    if charge_option["score"] > 0:
                        # if not min_soc_satisfied:
                        charge_index = soc_df_slice.loc[
                            soc_df_slice["timestep"]
                            >= charge_option["charge_event"].start_time
                        ].index
                        soc_df_slice.loc[
                            charge_index, "necessary_charging"
                        ] -= charge_option["delta_soc"]
                        min_soc_bool = soc_df_slice["necessary_charging"] <= 0
                        min_soc_satisfied = min_soc_bool.all()
                        total_charge += charge_option["delta_soc"]
                        veh.add_task(charge_option["charge_event"])
                        if "task_to" in charge_option:
                            veh.add_task(charge_option["task_to"])
                        if "task_from" in charge_option:
                            veh.add_task(charge_option["task_from"])

                        chosen_events.append(charge_option)
                        # TODO implement not choosing events if max charge is satisfied
                        # and they don't contribute to min_soc

                        if total_charge > max_charge and min_soc_satisfied:
                            break

                    else:
                        if min_soc_satisfied:
                            break
                        raise ValueError(
                            f"Not enough charging possible for vehicle {veh.id}!"
                        )

    def run(self):
        """Run the scenario with this strategy."""
        # create tasks for all vehicles from input schedule
        self._create_initial_schedule()
        # create charging tasks based on rating
        self._distribute_charging_slots(0, self.simulation.time_steps)
        # create save directory
        self.simulation.save_directory.mkdir(parents=True, exist_ok=True)

        # simulate fleet step by step
        for step in range(self.simulation.time_steps):
            # check all vehicles for tasks
            for veh in self.simulation.vehicles.values():
                task = veh.get_task(step)
                if task is None:
                    continue
                else:
                    self.execute_task(veh, task, step)

                veh.export(self.simulation.save_directory)
