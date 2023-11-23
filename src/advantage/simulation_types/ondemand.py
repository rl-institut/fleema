import pandas as pd
from operator import itemgetter

from advantage.simulation_type import SimulationType
from advantage.event import Status
from advantage.plot import plot
from advantage.event import Task
from advantage.util.conversions import datetime_string_to_datetime, step_to_timestamp


class Ondemand(SimulationType):
    def __init__(self, simulation):
        super().__init__(simulation)
        self.new_signal = False
        self.horizon = 30
        self.filtered_schedule = self.simulation.schedule.copy()
        self.new_tasks = []

    def run(self):
        """Run the scenario with this strategy."""
        # create tasks for all vehicles from input schedule
        self.simulation.vehicles_from_schedule()
        self.init_schedule()

        # create save directory
        if True in self.simulation.outputs.values():
            self.simulation.save_directory.mkdir(parents=True, exist_ok=True)
            self.save_inputs()

        # go through simulation time in steps
        for step in range(self.simulation.time_steps):
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
        window = start + self.horizon
        threshold_time = step_to_timestamp(self.simulation.time_series, window)
        start_time = step_to_timestamp(self.simulation.time_series, start)

        # filter out the tasks in the given window
        self.filtered_schedule['departure_time'] = pd.to_datetime(self.simulation.schedule['departure_time'])
        filtered_df = self.filtered_schedule[self.filtered_schedule['departure_time'] >= start_time]
        filtered_df = filtered_df[filtered_df['departure_time'] <= threshold_time]
        filtered_df['departure_time'] = filtered_df['departure_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # if no new driving tasks arrived, the schedule can remain the same
        if filtered_df.empty:
            # start 0 could have no driving tasks, so first it has to find charging events
            if start == 0:
                self.reschedule(start, window)
            return

        # if new driving tasks arrived, charging events have to be rescheduled
        filtered_df.apply(self.simulation.task_from_schedule, axis=1)
        filtered_df.apply(self.get_task, axis=1)
        self.reschedule(start, window)

    def reschedule(self, start, window):
        """Reschedule on behalf of the new incoming tasks."""
        # get break_list for every vehicle
        for veh in self.simulation.vehicles.values():
            break_list = veh.get_breaks(start, window)
            score_list = []

            # evaluate_charging_location -> every break that is at a charging_location, otherwise add parking_event
            for break_event in break_list:
                if break_event.start_point in self.simulation.charging_locations:
                    score = self.simulation.evaluate_charging_location(
                        veh.vehicle_type,
                        break_event.start_point,
                        break_event.start_point,
                        break_event.start_point,
                        break_event.start_time,
                        break_event.end_time,
                        veh.soc,
                    )
                    score_list.append(score)
                else:
                    veh.add_task(Task(
                        break_event.start_time,
                        break_event.end_time,
                        break_event.start_point,
                        break_event.start_point,
                        Status.PARKING,
                    ))
            score_list.sort(key=itemgetter("score"), reverse=True)
            # choose the best ones according to eval-score and soc_min
            while self.get_predicted_soc(veh, start, window) < self.simulation.soc_min:
                veh.add_task(score_list.pop()["charge_event"])

    def get_task(self, row):
        self.new_tasks.append((row["departure_time"], row["arrival_time"]))

    def init_schedule(self):
        # TODO: break_list is only one element?
        for veh in self.simulation.vehicles.values():
            break_list = veh.get_breaks(0, self.horizon)
            score_list = []

            # look at schedule to get location from first driving event and check if it is a charging location
            init_location_name = self.filtered_schedule.loc[self.filtered_schedule["vehicle_id"] == veh.id]["departure_name"].values[0]
            init_location = self.simulation.locations[init_location_name]
            if init_location in self.simulation.charging_locations:
                # evaluate_charging_location -> every break
                for break_event in break_list:
                    score = self.simulation.evaluate_charging_location(
                        veh.vehicle_type,
                        init_location,
                        break_event.start_time,
                        break_event.end_time,
                        veh.soc,
                    )
                    score_list.append(score)
                score_list.sort(key=itemgetter("score"), reverse=True)
                # choose the best ones according to eval-score and soc_min
                while self.get_predicted_soc(veh, 0, self.horizon) < self.simulation.soc_min:
                    veh.add_task(score_list.pop()["charge_event"])
            else:
                for break_event in break_list:
                    veh.add_task(Task(
                        break_event.start_time,
                        break_event.end_time,
                        init_location,
                        init_location,
                        Status.PARKING,
                    ))


def greedy_charging_schedule(electricity_cost, charging_time, charging_point_capacity, start_soc, end_of_day_soc):
    current_soc = start_soc
    total_cost = 0
    charging_schedule = []

    # Iterate until the end-of-day state of charge is reached
    while current_soc < end_of_day_soc:
        # Calculate the remaining needed charge
        remaining_charge = end_of_day_soc - current_soc

        # Calculate the maximum charge that can be added in the available charging time
        max_charge = min(remaining_charge, charging_point_capacity * charging_time)

        # Calculate the cost of the maximum charge
        charge_cost = max_charge * electricity_cost

        # Update variables
        current_soc += max_charge
        total_cost += charge_cost
        charging_schedule.append((max_charge, charge_cost))

    return charging_schedule, total_cost
