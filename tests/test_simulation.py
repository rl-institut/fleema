from advantage.simulation import Simulation

import pytest


def test_from_config():
    simulation = Simulation.from_config("cenario_data/bad_birnbach/configs/base_scenario.cfg")
    assert simulation.num_threads


def test_bad_config_name():
    scenario_name = "bad_name"
    with pytest.raises(
            FileNotFoundError,
            match=f"Scenario {scenario_name} not found in ./scenario_setting.",
    ):
        Simulation.from_config(scenario_name)


def test_run():
    simulation = Simulation.from_config("scenario_data/bad_birnbach/configs/base_scenario.cfg", no_outputs_mode=True)
    simulation.run()
    assert len(simulation.vehicles)
