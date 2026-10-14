import numpy as np
import pytest

from watersim import data, runoff


def test_no_runoff_below_initial_abstraction():
    rain = [1.0] * 5 + [0.0] * 30
    assert sum(runoff.scs_excess_rainfall(rain, curve_number=60)) == 0.0


def test_scs_event_total_matches_formula():
    cn = 80
    rain = [10.0] * 6
    s = 25400 / cn - 254
    p = sum(rain)
    expected = (p - 0.2 * s) ** 2 / (p + 0.8 * s)
    assert sum(runoff.scs_excess_rainfall(rain, cn)) == pytest.approx(expected)


def test_events_are_separated_by_dry_periods():
    rain = [20.0] * 3 + [0.0] * 30 + [20.0] * 3
    excess = runoff.scs_excess_rainfall(rain, 75)
    assert sum(excess[:3]) == pytest.approx(sum(excess[33:]))


def test_unit_hydrograph_volume_is_one_mm():
    uh = runoff.unit_hydrograph(area_km2=100.0, time_to_peak_h=10, length=200)
    volume_m3 = sum(uh) * 3600
    assert volume_m3 == pytest.approx(100.0 * 1e6 * 0.001)


def test_convolve_matches_numpy():
    rng = np.random.default_rng(0)
    excess = list(rng.random(300))
    uh = list(rng.random(40))
    expected = np.convolve(excess, uh)[:300]
    np.testing.assert_allclose(runoff.convolve(excess, uh), expected)


def test_moving_average():
    assert runoff.moving_average([1.0, 2.0, 3.0, 4.0, 5.0], 2) == pytest.approx([1.0, 1.5, 2.5, 3.5, 4.5])


def test_find_peaks():
    series = [0, 1, 5, 1, 0, 0, 7, 0, 0, 2, 0]
    assert runoff.find_peaks(series, half_window=2, threshold=3) == [2, 6]


def test_reference_results():
    summary = runoff.simulate(data.hourly_rainfall(3000))
    assert summary["hours"] == 3000
    assert summary["total_excess_mm"] == pytest.approx(128.2414, abs=1e-3)
    assert summary["peak_flow_m3s"] == pytest.approx(276.2538, abs=1e-3)
    assert summary["max_weekly_mean_m3s"] == pytest.approx(77.2343, abs=1e-3)
    assert summary["flood_peaks"] == 5
    assert summary["q10_m3s"] == pytest.approx(35.7946, abs=1e-3)
    assert summary["q90_m3s"] == pytest.approx(12.0, abs=1e-3)
