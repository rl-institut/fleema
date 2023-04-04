"""This script generates output plots.

Function
--------
plot
soc_plot

"""

import matplotlib.pyplot as plt

from advantage.simulation import Simulation


def soc_plot(simulation: "Simulation"):
    # data
    ts = simulation.time_series
    vehicles_soc_list = {
        key: [0 for _ in range(simulation.time_steps)]
        for key in simulation.vehicles.keys()
    }
    for veh in simulation.vehicles.keys():
        for event_start, soc in zip(
            simulation.vehicles[veh].output["event_start"],
            simulation.vehicles[veh].output["soc_start"],
        ):
            vehicles_soc_list[veh][event_start] = soc
        tmp_soc = 0
        for i in range(len(vehicles_soc_list[veh])):
            if vehicles_soc_list[veh][i] != 0:
                tmp_soc = vehicles_soc_list[veh][i]
            else:
                vehicles_soc_list[veh][i] = tmp_soc
    # plot
    fig, ax = plt.subplots()
    for veh in range(len(vehicles_soc_list)):
        ax.plot(ts, vehicles_soc_list[veh])
    ax.set_title("SOC of vehicles over time")
    ax.set_ylabel("SOC in percentage")
    fig.autofmt_xdate(rotation=45)
    ax.legend(simulation.vehicles.keys())
    fig.savefig(simulation.save_directory / "soc_timeseries.png")


def grid_timeseries(simulation: "Simulation"):
    """Generates plots for every grid (location) with the number of charging vehicles over time.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object that holds the grids (locations) with their "output" attribute.
    """
    for location in simulation.locations:
        output = simulation.locations[location].output
        if output is None:
            continue
        y = []
        if len(output) <= 2:
            y.append(output[f"{location}_total_power"])
        else:
            for key in output.keys():
                y.append(output[key])
        # plot
        fig, ax = plt.subplots()
        for plot_data in y:
            ax.plot(simulation.time_series, plot_data)
        ax.set_title("Grid Timeseries")
        ax.set_ylabel("Number of vehicles charging")
        fig.autofmt_xdate(rotation=45)
        ax.legend(output.keys())
        plt.savefig(simulation.save_directory / f"{location}_timeseries.png")
        plt.clf()


def energy_from_grid_vs_pv():
    pass


def plot(simulation, flag=False):
    """Generates all output plots and saves them in the output directory."""

    if flag:
        # soc_plot(simulation)
        grid_timeseries(simulation)
        energy_from_grid_vs_pv()
