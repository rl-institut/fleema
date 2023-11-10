from advantage.simulation_type import SimulationType
from advantage.event import Status


class Ondemand(SimulationType):
    def __init__(self, simulation):
        super().__init__(simulation)

    def evaluate_new_requests(self, veh):
        if veh.status == Status.DRIVING:
            return
        else:
            pass
            # wo wird geparkt, gebreakt oder gecharged?
            #

    def run(self):
        # create tasks for all vehicles from input schedule
        self._create_initial_schedule()
        # create save directory
        if True in self.simulation.outputs.values():
            self.simulation.save_directory.mkdir(parents=True, exist_ok=True)
            self.save_inputs()

        for step in range(self.simulation.time_steps):
            for veh in self.simulation.vehicles.values():
                # check the horizon and see if any changes regarding the schedule are required
                # horizon default=30min
                self.evaluate_new_requests(veh)

                task = veh.get_task(step)
                if task is None:
                    continue
                else:
                    self.execute_task(veh, task)

    def _create_initial_schedule(self):
        """Creates vehicles and tasks from the scenario schedule."""
        self.simulation.vehicles_from_schedule()
        # get tasks for every row of the schedule
        self.simulation.schedule.apply(self.simulation.task_from_schedule, axis=1)  # type: ignore
