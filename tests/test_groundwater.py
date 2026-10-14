import numpy as np
import pytest

from watersim import groundwater


def test_linear_profile_is_steady_without_sources():
    aquifer = groundwater.Aquifer(rows=10, cols=15, recharge=0.0)
    heads, _ = groundwater.simulate(aquifer, wells=[], steps=20)
    np.testing.assert_allclose(heads, groundwater.initial_heads(aquifer), atol=1e-9)


def test_boundaries_stay_fixed():
    aquifer = groundwater.Aquifer(rows=12, cols=12)
    wells = [groundwater.Well(6, 6, 1000.0)]
    heads, _ = groundwater.simulate(aquifer, wells, steps=30)
    np.testing.assert_allclose(heads[:, 0], aquifer.west_head)
    np.testing.assert_allclose(heads[:, -1], aquifer.east_head)


def test_pumping_creates_drawdown_at_well():
    aquifer = groundwater.Aquifer(rows=12, cols=12, recharge=0.0)
    wells = [groundwater.Well(6, 6, 1000.0)]
    heads, _ = groundwater.simulate(aquifer, wells, steps=30)
    start = groundwater.initial_heads(aquifer)
    drawdown = start - heads
    assert drawdown[6, 6] > 0.1
    assert drawdown[6, 6] == drawdown[1:-1, 1:-1].max()


def test_no_flow_boundaries_are_symmetric():
    aquifer = groundwater.Aquifer(rows=11, cols=11)
    wells = [groundwater.Well(5, 5, 800.0)]
    heads, _ = groundwater.simulate(aquifer, wells, steps=40)
    np.testing.assert_allclose(heads, heads[::-1, :], atol=1e-9)


def test_reference_results():
    aquifer = groundwater.Aquifer(rows=30, cols=30)
    wells = [groundwater.Well(10, 10, 500.0), groundwater.Well(20, 18, 800.0)]
    heads, days = groundwater.simulate(aquifer, wells, steps=60)
    summary = groundwater.summarise(aquifer, wells, heads, days)
    assert summary["simulated_days"] == pytest.approx(6.0)
    assert summary["mean_head_m"] == pytest.approx(95.01291, abs=1e-5)
    assert summary["max_drawdown_m"] == pytest.approx(0.77179, abs=1e-5)
