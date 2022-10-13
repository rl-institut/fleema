from advantage.simulation import Simulation


print("Running the ADVANTAGE tool...")
simulation = Simulation.from_config("public_transport_base")
simulation.run()
print("-- Done --")
