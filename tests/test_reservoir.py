import pytest

from watersim import data, reservoir


def flat_reservoir(area=1000.0):
    return reservoir.Reservoir(survey=[(0.0, area), (10.0, area)], crest_elevation=8.0,
                               spillway_width=5.0, weir_coefficient=1.7, outlet_area=0.5,
                               outlet_elevation=0.0, outlet_coefficient=0.6)


def test_storage_of_prismatic_basin():
    res = flat_reservoir(area=1000.0)
    assert reservoir.storage(res, 3.5) == pytest.approx(3500.0, rel=1e-6)


def test_storage_of_surveyed_reservoir_is_exact_for_linear_area():
    res = data.build_reservoir()
    a0, a1 = res.survey[0][1], res.survey[1][1]
    assert reservoir.storage(res, 101.0) == pytest.approx((a0 + a1) / 2, rel=1e-6)


def test_outflow_includes_spillway_above_crest():
    res = flat_reservoir()
    below = reservoir.outflow(res, 7.9)
    above = reservoir.outflow(res, 8.5)
    orifice_only = 0.6 * 0.5 * (2 * reservoir.GRAVITY * 8.5) ** 0.5
    assert above == pytest.approx(orifice_only + 1.7 * 5.0 * 0.5 ** 1.5)
    assert below < orifice_only


def test_volume_balance():
    res = data.build_reservoir()
    inflows = data.inflow_hydrograph(12, time_to_peak=4)
    elevations, outflows = reservoir.route(res, inflows, initial_elevation=118.0)
    dt = 3600.0
    volume_in = sum((a + b) / 2 * dt for a, b in zip(inflows, inflows[1:]))
    volume_out = sum((a + b) / 2 * dt for a, b in zip(outflows, outflows[1:]))
    delta_storage = reservoir.storage(res, elevations[-1]) - reservoir.storage(res, elevations[0])
    assert volume_in - volume_out == pytest.approx(delta_storage, rel=1e-4)


def test_reference_results():
    res = data.build_reservoir()
    inflows = data.inflow_hydrograph(12, time_to_peak=4)
    summary = reservoir.summarise(inflows, *reservoir.route(res, inflows, initial_elevation=118.0))
    assert summary["peak_outflow_m3s"] == pytest.approx(28.951, abs=2e-3)
    assert summary["attenuation_pct"] == pytest.approx(93.566, abs=2e-3)
    assert summary["max_elevation_m"] == pytest.approx(119.9866, abs=2e-4)
    assert summary["peak_delay_h"] == 7
