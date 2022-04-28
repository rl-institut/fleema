class Simulation:
    """
    This class can import a specified config directory and build the scenario. It also contains the run function,
    which starts the simulation.
    """

    def __init__(self, config_path=None):
        self.config_path = config_path

    def read_config(self):
        if self.config_path:
            return

    def run(self):
        pass