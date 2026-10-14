"""Rainfall-runoff: SCS curve number losses and unit hydrograph routing."""

import math
import statistics


def scs_excess_rainfall(rain, curve_number, dry_hours_between_events=24):
    """Hourly effective rainfall (mm) using the SCS-CN method per storm event."""
    retention = 25400 / curve_number - 254
    initial_abstraction = 0.2 * retention
    excess = []
    event_start = 0
    dry = 0
    for t, r in enumerate(rain):
        dry = dry + 1 if r == 0 else 0
        if dry >= dry_hours_between_events:
            event_start = t + 1
        cumulative_rain = sum(rain[event_start:t + 1])
        if cumulative_rain > initial_abstraction:
            cumulative_excess = (cumulative_rain - initial_abstraction) ** 2 / (
                cumulative_rain - initial_abstraction + retention)
        else:
            cumulative_excess = 0.0
        excess.append(max(0.0, cumulative_excess - sum(excess[event_start:t])))
    return excess


def unit_hydrograph(area_km2, time_to_peak_h, length):
    """Gamma-shaped 1-hour unit hydrograph (m3/s per mm of excess rain)."""
    shape = 3.7
    raw = []
    for t in range(length):
        x = (t + 0.5) / time_to_peak_h
        raw.append(x ** shape * math.exp(shape * (1 - x)))
    volume_per_mm = area_km2 * 1e6 * 0.001
    scale = volume_per_mm / (sum(raw) * 3600)
    return [v * scale for v in raw]


def convolve(excess, uh):
    runoff = []
    for t in range(len(excess)):
        total = 0.0
        for k in range(len(uh)):
            if t - k >= 0:
                total += excess[t - k] * uh[k]
        runoff = runoff + [total]
    return runoff


def moving_average(series, window):
    smoothed = []
    for i in range(len(series)):
        start = max(0, i - window + 1)
        smoothed.append(statistics.mean(series[start:i + 1]))
    return smoothed


def find_peaks(series, half_window, threshold):
    peaks = []
    for i in range(len(series)):
        window = series[max(0, i - half_window):i + half_window + 1]
        if series[i] >= threshold and series[i] == max(window) and i not in peaks:
            peaks.append(i)
    return peaks


def flow_duration_curve(series, points=1000):
    curve = []
    for p in range(1, points):
        exceedance = p / points
        ranked = sorted(series, reverse=True)
        curve.append((exceedance, ranked[int(exceedance * (len(ranked) - 1))]))
    return curve


def simulate(rain, area_km2=850.0, curve_number=72, time_to_peak_h=30, uh_length=240,
             baseflow=12.0):
    excess = scs_excess_rainfall(rain, curve_number)
    uh = unit_hydrograph(area_km2, time_to_peak_h, uh_length)
    direct = convolve(excess, uh)
    total = [baseflow + q for q in direct]
    smoothed = moving_average(total, 24 * 7)
    peaks = find_peaks(total, 72, threshold=3 * baseflow)
    fdc = flow_duration_curve(total)
    return {
        "hours": len(total),
        "total_excess_mm": round(sum(excess), 4),
        "peak_flow_m3s": round(max(total), 4),
        "max_weekly_mean_m3s": round(max(smoothed), 4),
        "flood_peaks": len(peaks),
        "q10_m3s": round(fdc[99][1], 4),
        "q90_m3s": round(fdc[899][1], 4),
    }
