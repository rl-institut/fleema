import pandas as pd
from operator import itemgetter

from advantage.simulation_type import SimulationType
from advantage.plot import plot
from advantage.util.conversions import step_to_timestamp


class Ondemand(SimulationType):
    def __init__(self, simulation):
        super().__init__(simulation)
        self.new_signal = False
        self.HORIZON = 30
        self.filtered_schedule = self.simulation.schedule.copy()

    def run(self):
        """Run the scenario with this strategy."""
        # create tasks for all vehicles from input schedule
        self.simulation.vehicles_from_schedule()

        # create save directory
        if True in self.simulation.outputs.values():
            self.simulation.save_directory.mkdir(parents=True, exist_ok=True)
            self.save_inputs()

        # go through simulation time in steps
        for step in range(self.simulation.time_steps):
            # look at new incoming driving tasks and change schedule accordingly
            self.evaluate_step(step)
            for veh in self.simulation.vehicles.values():
                task = veh.get_task(step)
                if task is None:
                    continue
                else:
                    self.execute_task(veh, task)
                veh.export(self.simulation.save_directory)
        self.vehicle_output()
        self.location_output()
        plot(self.simulation)

    def evaluate_step(self, start):
        # look in simulation.schedule if in the new window there are new tasks
        window = start + self.HORIZON
        threshold_time = step_to_timestamp(self.simulation.time_series, window)
        start_time = step_to_timestamp(self.simulation.time_series, start)

        # filter out the tasks in the given window
        self.filtered_schedule['departure_time'] = pd.to_datetime(self.simulation.schedule['departure_time']) # put into init_schedule()
        filtered_df = self.filtered_schedule[self.filtered_schedule['departure_time'] >= start_time]
        filtered_df = filtered_df[filtered_df['departure_time'] <= threshold_time]
        filtered_df['departure_time'] = filtered_df['departure_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # if no new driving tasks arrived, the schedule can remain the same
        if filtered_df.empty:
            # start 0 could have no driving tasks, so first it has to find charging events
            if start == 0:
                self.reschedule(start)
            return

        # if new driving tasks arrived, charging events have to be rescheduled
        filtered_df.apply(self.simulation.task_from_schedule, axis=1)
        self.reschedule(start)

    def reschedule(self, start):
        """Reschedule on behalf of the new incoming tasks."""
        # look for best charging events in all vehicles
        window = start + self.HORIZON
        for veh in self.simulation.vehicles.values():
            # initialize variables
            soc_df = self.get_predicted_soc(veh, start, window)
            break_list = veh.get_breaks(start, window)
            lowest_current_soc = veh.soc_start

            for counter, task in enumerate(break_list):
                # for all locations with chargers, evaluate the best option
                charging_list = []
                for loc in self.simulation.charging_locations:
                    soc_df_slice = soc_df.loc[soc_df["timestep"] >= task.start_time]
                    if len(soc_df_slice.index):
                        # get the lowest possible soc at this point in time (if no charging has happened)
                        lowest_current_soc = max(
                            soc_df_slice.iat[0, -1], self.simulation.soc_min
                        )
                    charging_list.append(
                        self.simulation.evaluate_charging_location(
                            veh.vehicle_type,
                            loc,
                            loc,
                            loc,
                            task.start_time,
                            task.end_time,
                            lowest_current_soc,
                        )
                    )
                # compare locations and choose the best one
                charging_list.sort(key=itemgetter("consumption"))
                charging_list.sort(
                    key=itemgetter("score", "delta_soc", "charge"), reverse=True
                )

            self.choose_best_charging_event(veh, start, charging_list)

    def choose_best_charging_event(self, vehicle, start, charging_list):
        # choose the best ones according to eval-score and soc_min
        predicted_soc = self.get_predicted_soc(vehicle, start, self.simulation.time_steps)["soc"].values[0]
        while predicted_soc < self.simulation.soc_min:
            vehicle.add_task(charging_list[0]["charge_event"])
            charging_list.pop()
            predicted_soc = self.get_predicted_soc(vehicle, start, self.simulation.time_steps)["soc"].values[0]
        # if vehicles can't charge for some reason, should it be just parking?
        """task = Task(
            start,
            start + self.HORIZON,

        )"""
