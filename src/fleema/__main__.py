from fleema.simulation import Simulation
import argparse


def main():
    """Main function of FLEEMA. Starts the program by parsing a scenario name from the command line."""
    parser = argparse.ArgumentParser(
        description="SimBEV modelling tool for generating timeseries of electric "
        "vehicles."
    )
    parser.add_argument(
        "config",
        default="scenario_data/bad_birnbach/configs/base_scenario.cfg",
        nargs="?",
        help="Set the scenario path from working directory (usually repository root).",
    )
    p_args = parser.parse_args()

    print("Running FLEEMA...")
    simulation = Simulation.from_config(p_args.config)
    simulation.run()
    print("-- Done --")


if __name__ == "__main__":
    main()
