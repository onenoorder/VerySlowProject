"""2D transient groundwater flow (explicit finite differences).

    S * dh/dt = T * (d2h/dx2 + d2h/dy2) + R - Q_wells / cell_area

Fixed heads on the west and east boundary, no-flow on north and south.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Well:
    row: int
    col: int
    rate: float


@dataclass
class Aquifer:
    rows: int
    cols: int
    cell_size: float = 50.0
    transmissivity: float = 500.0
    storativity: float = 0.1
    recharge: float = 0.001
    west_head: float = 100.0
    east_head: float = 90.0


def stable_time_step(aquifer):
    return 0.2 * aquifer.cell_size ** 2 * aquifer.storativity / aquifer.transmissivity


def initial_heads(aquifer):
    heads = np.zeros((aquifer.rows, aquifer.cols))
    for i in range(aquifer.rows):
        for j in range(aquifer.cols):
            fraction = j / (aquifer.cols - 1)
            heads[i, j] = aquifer.west_head + fraction * (aquifer.east_head - aquifer.west_head)
    return heads


def simulate(aquifer, wells, steps):
    dt = stable_time_step(aquifer)
    dx = aquifer.cell_size
    h = initial_heads(aquifer)

    for _ in range(steps):
        new_h = h.copy()
        for i in range(aquifer.rows):
            for j in range(aquifer.cols):
                if j == 0 or j == aquifer.cols - 1:
                    continue
                up = h[i - 1, j] if i > 0 else h[i + 1, j]
                down = h[i + 1, j] if i < aquifer.rows - 1 else h[i - 1, j]
                left = h[i, j - 1]
                right = h[i, j + 1]
                laplacian = (left + right + up + down - 4 * h[i, j]) / dx ** 2

                source = aquifer.recharge
                for well in wells:
                    if well.row == i and well.col == j:
                        source -= well.rate / dx ** 2

                new_h[i, j] = h[i, j] + dt / aquifer.storativity * (
                    aquifer.transmissivity * laplacian + source)
        h = new_h
    return h, dt * steps


def summarise(aquifer, wells, heads, elapsed_days):
    start = initial_heads(aquifer)
    drawdowns = [start[w.row, w.col] - heads[w.row, w.col] for w in wells]
    return {
        "simulated_days": round(elapsed_days, 3),
        "min_head_m": round(float(heads.min()), 5),
        "mean_head_m": round(float(heads.mean()), 5),
        "max_drawdown_m": round(float(max(drawdowns)), 5),
    }
