from fleema.simulation import Simulation
from fleema.event import Task, Status

import pytest


@pytest.fixture()
def simulation() -> Simulation:
    simulation = Simulation.from_config(
        "scenario_data/bad_birnbach/configs/base_scenario.cfg", no_outputs_mode=True
    )
    return simulation


def test_from_config(simulation):
    assert simulation.num_threads


def test_bad_config_name():
    scenario_path = "scenario_data/bad_birnbach/configs/bad_scenario_name_do_not_use_this_or_this_test_breaks.cfg"
    with pytest.raises(
        FileNotFoundError,
    ):
        Simulation.from_config(scenario_path)


# def test_run(simulation):
#     simulation.run()
#     assert len(simulation.vehicles)


def test_evaluate_charging_location(simulation):
    vehicle_type = simulation.vehicle_types["EZ10"]
    charging_location = simulation.locations["Marktplatz"]
    current_location = simulation.locations["Marktplatz"]
    next_location = simulation.locations["Marktplatz"]
    start_time = 0
    end_time = 100
    current_soc = 0.5
    expected_result = {
        "timestep": 0,
        "score": 0,  # Define expected score TODO
        "consumption": 0,  # Define expected consumption
        "charge": 0,  # Define expected charge TODO
        "delta_soc": 0,  # Define expected delta SoC TODO
        "charge_event": Task(
            0,
            100,
            simulation.locations["Marktplatz"],
            simulation.locations["Marktplatz"],
            Status.CHARGING,
            delta_soc=0.5,
        ),  # Define expected charge event task
        "task_to": None,  # Define expected task_to task
        "task_from": None,  # Define expected task_from task
    }
    # Call the function with test inputs
    result = simulation.evaluate_charging_location(
        vehicle_type,
        charging_location,
        current_location,
        next_location,
        start_time,
        end_time,
        current_soc,
    )

    # Assert that the result matches the expected result
    # assert result == expected_result
    assert result["consumption"] == expected_result["consumption"]
    # TODO more asserts
