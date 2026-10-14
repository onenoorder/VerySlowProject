import numpy as np
import pytest

from watersim import data, watershed


def test_simple_slope_accumulates_downhill():
    dem = np.array([
        [5.0, 5.0, 5.0],
        [4.0, 4.0, 4.0],
        [3.0, 2.0, 3.0],
    ])
    directions, accumulation = watershed.flow_accumulation(dem)
    assert directions[2, 1] == -1
    assert accumulation[2, 1] == 9
    assert accumulation[0, 0] == 1


def test_outlets_collect_every_cell():
    dem = data.build_dem(25, 25)
    directions, accumulation = watershed.flow_accumulation(dem)
    outlet_total = accumulation[directions < 0].sum()
    assert outlet_total == dem.size


def test_accumulation_grows_downstream():
    dem = data.build_dem(20, 20)
    directions, accumulation = watershed.flow_accumulation(dem)
    rows, cols = dem.shape
    for r in range(rows):
        for c in range(cols):
            down = watershed.downstream_cell(directions, r, c)
            if down is not None:
                assert accumulation[down] > accumulation[r, c]


def test_reference_results():
    dem = data.build_dem(30, 30)
    summary = watershed.summarise(dem, *watershed.flow_accumulation(dem))
    assert summary == {
        "cells": 900,
        "outlets": 3,
        "stream_cells": 62,
        "max_accumulation": 638,
        "largest_outlet": (29, 14),
    }
