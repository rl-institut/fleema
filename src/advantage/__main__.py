"""
This script starts the simulation.

The simulation is instantiated by using the scenario name from the command line.
"""

from advantage.simulation import Simulation


print("Running the ADVANTAGE tool...")
simulation = Simulation.from_config("public_transport_base")
print("-- Done --")
