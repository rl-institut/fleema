from advantage.simulation import Simulation

import pytest


def test_from_config():
    simulation = Simulation.from_config("scenario_data/bad_birnbach/configs/base_scenario.cfg")
    assert simulation.num_threads


def test_bad_config_name():
    scenario_path = "scenario_data/bad_birnbach/configs/bad_scenario.cfg"
    with pytest.raises(
            FileNotFoundError,
            match=f"Config file {scenario_path} not found.",
    ):
        Simulation.from_config(scenario_path)


def test_run():
    simulation = Simulation.from_config("scenario_data/bad_birnbach/configs/base_scenario.cfg", no_outputs_mode=True)
    simulation.run()
    assert len(simulation.vehicles)
