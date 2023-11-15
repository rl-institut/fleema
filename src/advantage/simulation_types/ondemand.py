from advantage.simulation_type import SimulationType
from advantage.event import Status
from advantage.plot import plot
from advantage.event import Task


class Ondemand(SimulationType):
    def __init__(self, simulation):
        super().__init__(simulation)

    def initialize_charging_events(self, start: int, end_soc: float, horizon=30):
        # jetzt gibt es nur driving tasks
        # breaklist erstellen
        # aus breaklist bestes charging schedule finden
        for veh in self.simulation.vehicles.values():
                # für jedes vehikel die charging events finden, mit Horizont -> start, end und end_soc
                soc_df = self.get_predicted_soc(veh, start, horizon)
                break_list = veh.get_breaks(start, horizon)

                # self.get_charging_events(break_list, soc_df, veh)
                for break_event in break_list:
                    task = Task(
                        start,
                        start + horizon,
                        break_event.start_point,
                        break_event.start_point,
                        Status.CHARGING,
                    )
                    veh.add_task(task)

    def evaluate_step(self, start):
        pass
        # check if cs capacity is available --> location.is_available()
        # dann durch alle kollidierenden charging events (selbe Zeit, selbe cs-location) gehen
        # und aufteilen nach variables
        horizon = 30
        collisions = []
        for step in range(start+horizon):
            for veh in self.simulation.vehicles:
                task = veh.get_task(step)


        # variables:
            # electricity cost
            # available charging time
            # charging point capacity
            # charging value
            # soc
            # end-of-day soc

        # Plan für neue Tasks für den nächsten Horizont erstellen
        # kollidierende Tasks anschauen und entsprechend Plan modifizieren
        #

    def run(self):
        # create tasks for all vehicles from input schedule
        self._create_initial_schedule()
        # create save directory
        if True in self.simulation.outputs.values():
            self.simulation.save_directory.mkdir(parents=True, exist_ok=True)
            self.save_inputs()

        self.initialize_charging_events(0, self.simulation.time_steps, self.simulation.end_of_day_soc)
        for step in range(self.simulation.time_steps):
            for veh in self.simulation.vehicles.values():
                task = veh.get_task(step)
                if task is None:
                    continue
                else:
                    # check the horizon and see if any changes regarding the schedule are required
                    self.evaluate_step(step)
                    self.execute_task(veh, task)
                veh.export(self.simulation.save_directory)
        self.vehicle_output()
        self.location_output()
        plot(self.simulation)

    def _create_initial_schedule(self):
        """Creates vehicles and tasks from the scenario schedule."""
        self.simulation.vehicles_from_schedule()
        # get tasks for every row of the schedule
        self.simulation.schedule.apply(self.simulation.task_from_schedule, axis=1)  # type: ignore


def greedy_charging_schedule(electricity_cost, charging_time, charging_point_capacity, start_soc, end_of_day_soc):
    # Initialize variables
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
