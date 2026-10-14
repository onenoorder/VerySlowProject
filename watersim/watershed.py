"""Surface drainage on a digital elevation model (D8 method)."""

import math

import numpy as np

NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def flow_directions(dem):
    """Index into NEIGHBOURS of the steepest downhill neighbour, -1 for pits/outlets."""
    rows, cols = dem.shape
    directions = np.full((rows, cols), -1, dtype=int)
    for r in range(rows):
        for c in range(cols):
            best_slope = 0.0
            for k, (dr, dc) in enumerate(NEIGHBOURS):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    slope = (dem[r, c] - dem[nr, nc]) / math.hypot(dr, dc)
                    if slope > best_slope:
                        best_slope = slope
                        directions[r, c] = k
    return directions


def downstream_cell(directions, r, c):
    k = directions[r, c]
    if k < 0:
        return None
    dr, dc = NEIGHBOURS[k]
    return (r + dr, c + dc)


def upstream_cells(directions, r, c):
    """All cells (including the cell itself) that drain through (r, c)."""
    rows, cols = directions.shape
    result = [(r, c)]
    queue = [(r, c)]
    while queue:
        cr, cc = queue.pop(0)
        for dr, dc in NEIGHBOURS:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if downstream_cell(directions, nr, nc) == (cr, cc) and (nr, nc) not in result:
                    result.append((nr, nc))
                    queue.append((nr, nc))
    return result


def flow_accumulation(dem):
    directions = flow_directions(dem)
    rows, cols = dem.shape
    accumulation = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            accumulation[r, c] = len(upstream_cells(directions, r, c))
    return directions, accumulation


def summarise(dem, directions, accumulation, stream_threshold=50):
    rows, cols = dem.shape
    outlets = [(r, c) for r in range(rows) for c in range(cols) if directions[r, c] < 0]
    streams = [(r, c) for r in range(rows) for c in range(cols)
               if accumulation[r, c] >= stream_threshold]
    largest = max(outlets, key=lambda cell: accumulation[cell])
    return {
        "cells": rows * cols,
        "outlets": len(outlets),
        "stream_cells": len(streams),
        "max_accumulation": int(accumulation.max()),
        "largest_outlet": tuple(int(v) for v in largest),
    }
