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
import pandas as pd
import plotly.express as px

from advantage.simulation import Simulation


def soc_plot(simulation: "Simulation"):
    """Plots the SOC (state of charge) of all vehicles over the simulated time.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object with the vehicles and their socs.
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
    # matplotlib
    fig, ax = plt.subplots()
    for veh in range(len(vehicles_soc_list)):
        ax.plot(simulation.time_series, vehicles_soc_list[veh])
    ax.set_title("SOC of vehicles over time")
    ax.set_ylabel("SOC in percentage")
    fig.autofmt_xdate(rotation=45)
    ax.legend(simulation.vehicles.keys())
    fig.savefig(simulation.save_directory / "plots" / "soc_timeseries.png")

    # plotly
    df = pd.DataFrame()
    for veh in vehicles_soc_list.keys():
        tmp_df = pd.DataFrame(
            {
                "time": simulation.time_series,
                veh: vehicles_soc_list[veh],
                "type": [veh for _ in range(simulation.time_steps)],
            }
        )
        tmp_df.rename(columns={veh: "soc"}, inplace=True)
        df = pd.concat([df, tmp_df])
    fig = px.line(
        df,
        x="time",
        y="soc",
        color="type",
        title="SOC of vehicles over time",
        template="seaborn",
    )
    fig.write_html(simulation.save_directory / "plots/html" / "soc_timeseries.html")


def grid_timeseries(simulation: "Simulation"):
    """Generates plots for every grid (location) with the energy charging over time.

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
    plt.savefig(simulation.save_directory / "plots" / "total_power_timeseries.png")
    plt.clf()

    # timeseries by location (grid)
    single_df = pd.DataFrame()
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
        # matplotlib
        fig, ax = plt.subplots()
        for plot_data in y:
            ax.plot(simulation.time_series, plot_data)
        ax.set_title(f"{location} Grid Timeseries")
        ax.set_ylabel("kWh")
        fig.autofmt_xdate(rotation=45)
        plt.savefig(simulation.save_directory / "plots" / f"{location}_timeseries.png")
        plt.clf()

        # plotly
        # total grid
        total_df = pd.DataFrame(
            {
                "time": simulation.time_series,
                "total power": simulation.outputs["total_power"],
            }
        )
        fig = px.line(total_df, x="time", y="total power", title="Total Power")
        fig.write_html(
            simulation.save_directory / "plots/html" / "total_power_timeseries.html"
        )
        # single grid
        single_df = pd.DataFrame()
        for loc in simulation.locations:
            output = simulation.locations[loc].output
            if output is None:
                continue
            tmp_df = pd.DataFrame(
                {
                    "time": simulation.time_series,
                    "values": output[f"{loc}_total_power"],
                    "type": [loc for _ in range(simulation.time_steps)],
                }
            )
            single_df = pd.concat([single_df, tmp_df])
        fig = px.line(
            single_df,
            x="time",
            y="values",
            color="type",
            title="Individual Power Timeseries",
            template="seaborn",
        )
        fig.write_html(
            simulation.save_directory
            / "plots/html"
            / "individual_power_timeseries.html"
        )


def energy_from_grid_feedin(simulation: "Simulation"):
    """Generates a pie-chart with the distribution of the energy in grid and feed-in.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object with vehicles and its drawn energy.
    """
    grid_and_feedin = [0, 0]
    for vehicle in simulation.vehicles.keys():
        grid_and_feedin[0] += sum(
            simulation.vehicles[vehicle].output["energy_from_grid"]
        )
        grid_and_feedin[1] += sum(
            simulation.vehicles[vehicle].output["energy_from_feed_in"]
        )
    # matplotlib
    fig, ax = plt.subplots()
    ax.set_title("Energy Distribution")
    ax.pie(grid_and_feedin, labels=["Grid", "Feed-in"], autopct="%1.1f%%")
    fig.savefig(simulation.save_directory / "plots" / "energy_distribution.png")
    plt.clf()

    # plotly
    df = {"energy value": grid_and_feedin, "energy type": ["grid", "feed-in"]}
    fig = px.pie(
        df,
        values="energy value",
        names="energy type",
        title="Energy Distribution",
        template="seaborn",
    )
    fig.write_html(
        simulation.save_directory / "plots/html" / "energy_distribution.html"
    )


def plot(simulation: "Simulation", flag=False):
    """Generates all output plots and saves them in the output directory.

    Parameters
    ----------
    simulation : Simulation
        The current simulation object
    flag : bool
        Is to be changed in the config and decides if the plots are being generated. Default is False.
    """
    if flag:
        pathlib.Path(simulation.save_directory / "plots").mkdir(
            parents=True, exist_ok=True
        )
        pathlib.Path(simulation.save_directory / "plots/html").mkdir(
            parents=True, exist_ok=True
        )
        # matplotlib and plotly
        soc_plot(simulation)
        grid_timeseries(simulation)
        energy_from_grid_feedin(simulation)
