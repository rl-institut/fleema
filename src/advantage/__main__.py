"""
This script starts the simulation.

The imported class Simulation is instantiated by inserting the scenario into the appropriation configuration method.
"""

from advantage.simulation import Simulation


print("Running the ADVANTAGE tool...")
simulation = Simulation.from_config("public_transport_base")
print("-- Done --")
