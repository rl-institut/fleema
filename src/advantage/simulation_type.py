from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advantage.simulation import Simulation

def class_from_str(strategy_name):
    import_name = strategy_name.lower()
    class_name = "".join([s.capitalize() for s in strategy_name.split('_')])
    module = import_module('advantage.simulation_types.' + import_name)
    return getattr(module, class_name)


class SimulationType:
    """

    """

    def __init__(self, simulation: "Simulation"):
        self.simulation = simulation
