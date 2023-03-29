"""This script generates output plots.

"""

import pathlib
import matplotlib.pyplot as plt
import pandas as pd

from advantage.simulation import Simulation


def soc_plot(simulation: "Simulation"):
	# data
	ts = simulation.time_series
	vehicles_soc_list = {key: [0 for _ in range(simulation.time_steps)] for key in simulation.vehicles.keys()}
	for veh in simulation.vehicles.keys():
		for event_start, soc in zip(simulation.vehicles[veh].output["event_start"], simulation.vehicles[veh].output["soc_start"]):
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
	# plt.xticks(rotation=45)
	fig.autofmt_xdate(rotation=45)
	ax.legend(simulation.vehicles.keys())
	fig.savefig(simulation.save_directory / "soc_timeseries.png")


def grid_timeseries():
	pass


def energy_from_grid_vs_pv():
	pass


def plot(simulation, flag=False):
	"""Generates all output plots and saves them in the output directory.

	"""
	soc_plot(simulation)
	grid_timeseries()
	energy_from_grid_vs_pv()
