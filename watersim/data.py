"""Deterministic synthetic input data for all WaterSim cases."""

import csv
import math
import os
import random
from datetime import datetime, timedelta

import numpy as np

from watersim.pipe_network import Network, Pipe
from watersim.reservoir import Reservoir
from watersim.river import Channel


def build_grid_network(loops_x, loops_y, seed=42):
    """Build a rectangular looped pipe network fed from the top-left node."""
    rng = random.Random(seed)
    cols, rows = loops_x + 1, loops_y + 1

    def node_id(r, c):
        return r * cols + c

    demands = {}
    for r in range(rows):
        for c in range(cols):
            demands[node_id(r, c)] = 0.0 if (r, c) == (0, 0) else round(rng.uniform(0.0005, 0.002), 6)
    demands[0] = -sum(demands.values())

    pipes = []
    for r in range(rows):
        for c in range(cols - 1):
            pipes.append(Pipe(f"H{r}_{c}", node_id(r, c), node_id(r, c + 1),
                              length=round(rng.uniform(100, 400), 1),
                              diameter=rng.choice([0.15, 0.2, 0.25, 0.3]),
                              roughness=0.00015))
    for r in range(rows - 1):
        for c in range(cols):
            pipes.append(Pipe(f"V{r}_{c}", node_id(r, c), node_id(r + 1, c),
                              length=round(rng.uniform(100, 400), 1),
                              diameter=rng.choice([0.15, 0.2, 0.25, 0.3]),
                              roughness=0.00015))

    by_id = {p.id: p for p in pipes}
    for c in range(cols):
        for r in range(rows - 1):
            by_id[f"V{r}_{c}"].flow = sum(demands[node_id(rr, c)] for rr in range(r + 1, rows))
    for c in range(cols - 1):
        by_id[f"H0_{c}"].flow = sum(demands[node_id(rr, cc)]
                                    for cc in range(c + 1, cols) for rr in range(rows))

    loops = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            loops.append([(f"H{r}_{c}", 1), (f"V{r}_{c + 1}", 1),
                          (f"H{r + 1}_{c}", -1), (f"V{r}_{c}", -1)])

    return Network(nodes=demands, pipes=pipes, loops=loops)


def build_river_reaches():
    """A river split into reaches with different cross sections."""
    return [
        Channel("Upper gorge", bottom_width=12.0, side_slope=0.5, manning_n=0.03, bed_slope=0.015),
        Channel("Middle meander", bottom_width=25.0, side_slope=2.0, manning_n=0.035, bed_slope=0.0008),
        Channel("Lower canal", bottom_width=40.0, side_slope=1.5, manning_n=0.025, bed_slope=0.0003),
    ]


def daily_discharge(days, seed=7):
    """Synthetic daily river discharge (m3/s) with a few flood waves."""
    rng = random.Random(seed)
    flows = []
    for d in range(days):
        seasonal = 60 + 40 * math.sin(2 * math.pi * d / 365)
        flood = 0.0
        for peak_day, peak in ((20, 450), (55, 700), (80, 300)):
            flood += peak * math.exp(-((d - peak_day) / 4.0) ** 2)
        flows.append(round(seasonal + flood + rng.uniform(-5, 5), 3))
    return flows


def build_dem(rows, cols, seed=3):
    """Valley-shaped terrain (m) draining towards the bottom-centre."""
    rng = np.random.default_rng(seed)
    r = np.arange(rows).reshape(-1, 1)
    c = np.arange(cols).reshape(1, -1)
    mid = (cols - 1) / 2
    dem = 200.0 + (rows - r) * 1.0 + 0.6 * np.abs(c - mid) + 3.0 * np.sin(c / 5.0) * np.cos(r / 7.0)
    dem += rng.uniform(-0.3, 0.3, size=(rows, cols))
    return dem


def hourly_rainfall(hours, seed=11):
    """Synthetic hourly rainfall (mm) with random storm events."""
    rng = random.Random(seed)
    rain = [0.0] * hours
    t = 0
    while t < hours:
        t += rng.randint(48, 400)
        duration = rng.randint(3, 36)
        intensity = rng.uniform(0.5, 8.0)
        for k in range(duration):
            if t + k < hours:
                shape = math.sin(math.pi * (k + 0.5) / duration)
                rain[t + k] = round(intensity * shape * rng.uniform(0.5, 1.5), 3)
        t += duration
    return rain


def build_reservoir():
    """A reservoir with a surveyed area-elevation table (elevation m, area m2)."""
    survey = []
    for i in range(31):
        z = 100.0 + i * 1.0
        area = 200_000 + 90_000 * i + 6_500 * i * i
        survey.append((z, float(area)))
    return Reservoir(survey=survey, crest_elevation=124.0, spillway_width=30.0,
                     weir_coefficient=1.7, outlet_area=2.5, outlet_elevation=101.0,
                     outlet_coefficient=0.6)


def inflow_hydrograph(steps, base=15.0, peak=450.0, time_to_peak=18):
    """Gamma-shaped flood inflow (m3/s) at hourly steps."""
    flows = []
    for t in range(steps):
        x = t / time_to_peak
        flows.append(base + (peak - base) * (x ** 3) * math.exp(3 * (1 - x)))
    return flows


def write_sensor_files(folder, stations, hours, seed=5):
    """Write stations.csv and sensor_readings.csv; returns their paths."""
    rng = random.Random(seed)
    os.makedirs(folder, exist_ok=True)
    stations_path = os.path.join(folder, "stations.csv")
    readings_path = os.path.join(folder, "sensor_readings.csv")

    station_rows = []
    for s in range(stations):
        station_rows.append({
            "station_id": f"ST{s:03d}",
            "name": f"Gauge {s}",
            "river": rng.choice(["Rhine", "Meuse", "IJssel", "Waal", "Lek"]),
            "alarm_level_m": round(rng.uniform(2.6, 3.0), 2),
        })
    with open(stations_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(station_rows[0].keys()))
        writer.writeheader()
        writer.writerows(station_rows)

    start = datetime(2026, 1, 1)
    rows = []
    for h in range(hours):
        ts = (start + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S")
        for s in range(stations):
            level = 2.0 + 0.8 * math.sin(2 * math.pi * (h + 13 * s) / 240) + rng.uniform(-0.05, 0.05)
            if rng.random() < 0.003:
                level += rng.uniform(3, 6)
            flow = 35.0 * max(level, 0.1) ** 1.6
            row = [f"ST{s:03d}", ts, f"{level:.3f}", f"{flow:.3f}"]
            rows.append(row)
            if rng.random() < 0.01:
                rows.append(list(row))
    with open(readings_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["station_id", "timestamp", "water_level_m", "flow_m3s"])
        writer.writerows(rows)
    return stations_path, readings_path
