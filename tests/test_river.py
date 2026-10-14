import pytest

from watersim import data, river

CANAL = river.Channel("test canal", bottom_width=10.0, side_slope=1.0, manning_n=0.03, bed_slope=0.001)


@pytest.mark.parametrize("discharge", [5.0, 50.0, 250.0])
def test_normal_depth_reproduces_discharge(discharge):
    depth = river.normal_depth(CANAL, discharge)
    assert river.manning_discharge(CANAL, depth) == pytest.approx(discharge, rel=1e-3)


@pytest.mark.parametrize("discharge", [5.0, 50.0, 250.0])
def test_froude_is_one_at_critical_depth(discharge):
    depth = river.critical_depth(CANAL, discharge)
    assert river.froude_number(CANAL, discharge, depth) == pytest.approx(1.0, rel=1e-3)


def test_rectangular_critical_depth_matches_formula():
    channel = river.Channel("rect", bottom_width=8.0, side_slope=0.0, manning_n=0.03, bed_slope=0.001)
    q = 40.0
    expected = ((q / 8.0) ** 2 / river.GRAVITY) ** (1 / 3)
    assert river.critical_depth(channel, q) == pytest.approx(expected, abs=2e-4)


def test_reference_results():
    reaches = data.build_river_reaches()
    discharges = data.daily_discharge(30)[15:30]
    summary = river.summarise(river.analyse_reaches(reaches, discharges))
    assert summary["rows"] == 45
    assert summary["max_depth_m"] == pytest.approx(6.3646, abs=2e-4)
    assert summary["max_velocity_ms"] == pytest.approx(8.2924, rel=1e-3)
    assert summary["supercritical_rows"] == 15
    assert summary["flood_days"] == 9
