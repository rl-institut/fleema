from advantage.simulation import Simulation

# TODO implement argparse for scenario
print("Running the ADVANTAGE tool...")
simulation = Simulation.from_config("public_transport_base")
simulation.run()
print("-- Done --")
