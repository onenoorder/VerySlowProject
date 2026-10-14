import math

import pytest

from watersim import data, pipe_network


@pytest.fixture(scope="module")
def solved_network():
    network = data.build_grid_network(3, 3)
    result = pipe_network.analyse(network)
    return network, result


@pytest.mark.parametrize("reynolds, rel_roughness, expected", [
    (1e5, 0.0, 0.01799),
    (1e5, 0.001, 0.02218),
    (1e6, 0.0001, 0.01344),
])
def test_colebrook_friction_factor(reynolds, rel_roughness, expected):
    assert pipe_network.friction_factor(reynolds, rel_roughness) == pytest.approx(expected, rel=1e-3)


def test_laminar_friction_factor():
    assert pipe_network.friction_factor(1000, 0.001) == pytest.approx(0.064)


def test_friction_factor_is_continuous_in_transition_zone():
    below = pipe_network.friction_factor(3999.999, 0.001)
    above = pipe_network.friction_factor(4000.001, 0.001)
    assert below == pytest.approx(above, rel=1e-4)


def test_mass_is_conserved_at_every_node(solved_network):
    network, result = solved_network
    assert result["continuity_error"] < 1e-12


def test_head_losses_balance_around_each_loop(solved_network):
    network, _ = solved_network
    pipes = {p.id: p for p in network.pipes}
    for loop in network.loops:
        total = sum(pipe_network.head_loss(pipes[pid], d * pipes[pid].flow) for pid, d in loop)
        assert abs(total) < 1e-4


def test_reference_results(solved_network):
    _, result = solved_network
    assert result["min_head_m"] == pytest.approx(59.8962, abs=1e-3)
    assert result["max_velocity_ms"] == pytest.approx(0.218, abs=1e-3)
    assert result["total_supply_m3s"] == pytest.approx(0.01591, abs=1e-6)


def test_head_loss_sign_follows_flow():
    pipe = pipe_network.Pipe("P", 0, 1, length=100, diameter=0.2, roughness=0.00015)
    assert pipe_network.head_loss(pipe, 0.02) > 0
    assert pipe_network.head_loss(pipe, -0.02) == pytest.approx(-pipe_network.head_loss(pipe, 0.02))
    assert math.isclose(pipe_network.head_loss(pipe, 0.0), 0.0)
