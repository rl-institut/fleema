class Simulation:
    """
    This class can import a specified config directory and build the scenarios.
    It also contains the run function, which starts the simulation.
    """

    def __init__(self, config_path):
        self.config_path = config_path
        self.read_config()

    def read_config(self):
        if self.config_path:
            return

    def run(self):
        pass