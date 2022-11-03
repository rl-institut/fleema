from advantage.simulation import Simulation
import argparse


def main():
    parser = argparse.ArgumentParser(description="SimBEV modelling tool for generating timeseries of electric "
                                                 "vehicles.")
    parser.add_argument("scenario", default="public_transport_base", nargs='?',
                        help="Set the scenario which is located in ./scenarios .")
    p_args = parser.parse_args()

    print("Running the ADVANTAGE tool...")
    simulation = Simulation.from_config(p_args.scenario)
    simulation.run()
    print("-- Done --")


if __name__ == "__main__":
    main()
