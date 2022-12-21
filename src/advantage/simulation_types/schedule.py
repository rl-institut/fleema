from advantage.simulation_type import SimulationType
from advantage.util.conversions import step_to_timestamp
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advantage.simulation import Simulation


class Schedule(SimulationType):
    def __init__(self, simulation: "Simulation"):
        super().__init__(simulation)

    def _create_initial_schedule(self):
        # creates tasks from self.schedule and assigns them to the vehicles
        # creates self.events: List of timesteps where an event happens
        # TODO check similar functions in ebus toolbox
        self.simulation.vehicles_from_schedule()
        # get tasks for every row of the schedule
        self.simulation.schedule.apply(self.simulation.task_from_schedule, axis=1)  # type: ignore

    def _distribute_charging_slots(self, start, end):
        # go through all vehicles, check SoC after all tasks (end of day). continues if <20%
        # evaluate charging slots
        # distribute slots by highest total score (?)
        # for conflicts, check amount of charging spots at location and total possible power
        for veh in self.simulation.vehicles.values():
            soc_df = self.get_predicted_soc(veh, start, end)
            break_list = veh.get_breaks(start, end)
            charging_list = []
            for task in break_list:
                # for all locations with chargers, evaluate the best option. save task, best location, evaluation
                # self.simulation.evaluate_charging_location()
                for loc in self.simulation.charging_locations:
                    charging_list.append(
                        self.simulation.evaluate_charging_location(
                            veh.vehicle_type,
                            loc,
                            task.start_point,
                            task.end_point,
                            task.start_time,
                            task.end_time,
                            0.0,
                        )
                    )
                    # TODO compare evaluation to necessary charging energy
                    # TODO make charging list, create vehicle function to parse list into tasks
            # check if end of day soc is below minimum soc
            if soc_df.iat[-1, 1] < self.simulation.soc_min:
                pass
            else:
                pass

    def run(self):
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
                    if task.task == "driving":
                        if not task.is_calculated:
                            trip = self.simulation.driving_sim.calculate_trip(
                                task.start_point,
                                task.end_point,
                                veh.vehicle_type,
                            )
                            task.delta_soc = trip["soc_delta"]
                            task.float_time = trip["trip_time"]
                        veh.drive(
                            step_to_timestamp(self.simulation.time_series, step),
                            task.start_time,
                            task.end_time - task.start_time,
                            task.end_point,
                            veh.soc + task.delta_soc,
                            self.simulation.observer,
                        )
                veh.export(self.simulation.save_directory)
