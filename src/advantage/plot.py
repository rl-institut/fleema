"""This script generates output plots.

Functions
---------
soc_plot
grid_timeseries
energy_from_grid_vs_pv
plot

"""

import pathlib
import matplotlib.pyplot as plt

from advantage.simulation import Simulation


def soc_plot(simulation: "Simulation"):
    """Plots the SOC (state of charge) of all vehicles over the simulated time.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object that holds the grids (locations) with their "output" attribute.
    """
    # data
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
        ax.plot(simulation.time_series, vehicles_soc_list[veh])
    ax.set_title("SOC of vehicles over time")
    ax.set_ylabel("SOC in percentage")
    fig.autofmt_xdate(rotation=45)
    ax.legend(simulation.vehicles.keys())
    fig.savefig(simulation.save_directory / "plots" / "soc_timeseries.png")


def grid_timeseries(simulation: "Simulation"):
    """Generates plots for every grid (location) with the number of charging vehicles over time.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object that holds the grids (locations) with their "output" attribute.
    """
    # total grid timeseries
    fig, ax = plt.subplots()
    ax.plot(simulation.time_series, simulation.outputs["total_power"])
    ax.set_title("Total Power Grid Timeseries")
    ax.set_ylabel("kWh")
    fig.autofmt_xdate(rotation=45)
    plt.savefig(simulation.save_directory / "plots" / "Total_power_timeseries.png")
    plt.clf()

    # timeseries by location (grid)
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
        ax.set_title(f"{location} Grid Timeseries")
        ax.set_ylabel("kWh")
        fig.autofmt_xdate(rotation=45)
        plt.savefig(simulation.save_directory / "plots" / f"{location}_timeseries.png")
        plt.clf()


def energy_from_grid_vs_feed_in(simulation):
    pass


def plot(simulation, flag=False):
    """Generates all output plots and saves them in the output directory.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object
    flag : bool
        Is to be changed in the config and decides if the plots are being generated. Default is False.
    """
    if flag:
        pathlib.Path(simulation.save_directory / "plots").mkdir(parents=True, exist_ok=True)
        soc_plot(simulation)
        grid_timeseries(simulation)
        energy_from_grid_vs_feed_in(simulation)
