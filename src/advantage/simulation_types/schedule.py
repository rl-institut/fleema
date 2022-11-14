from advantage.simulation_type import SimulationType
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
        # TODO write vehicle function end_of_day_soc()
        # get possible charging slots
        # TODO write vehicle function get_breaks(Optional param time_horizon, default end of day)
        # evaluate charging slots
        # distribute slots by highest total score (?)
        # for conflicts, check amount of charging spots at location and total possible power
        for veh in self.simulation.vehicles.values():
            end_of_day_soc = veh.get_predicted_soc(start, end)
            break_list = veh.get_breaks(start, end)
            for task in break_list:
                # for all locations with chargers, evaluate the best option. save task, best location, evaluation
                # self.simulation.evaluate_charging_location()
                pass
            if end_of_day_soc < 0.2:
                pass
            else:
                pass

    def run(self):
        self._create_initial_schedule()
        self._distribute_charging_slots(0, self.simulation.time_steps)
        # TODO start fleet management (includes loop)
        for step in range(self.simulation.time_steps):
            if len(self.simulation.events) and not self.simulation.events[0] == step:
                continue
            # start all current tasks (charge, drive)
            pass
