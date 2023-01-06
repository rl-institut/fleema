from advantage.simulation import Simulation

import pytest


def test_from_config():
    simulation = Simulation.from_config("bad_birnbach")
    assert simulation.num_threads


def test_bad_config_name():
    scenario_name = "bad_name"
    with pytest.raises(
        FileNotFoundError, match="Scenario bad_name not found in ./scenarios."
    ):
        Simulation.from_config(scenario_name)


def test_run():
    simulation = Simulation.from_config("bad_birnbach", no_outputs_mode=True)
    simulation.run()
    assert len(simulation.vehicles)
