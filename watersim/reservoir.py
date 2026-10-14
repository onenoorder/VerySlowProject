"""Level-pool reservoir flood routing (modified Puls method)."""

import math
from dataclasses import dataclass

GRAVITY = 9.81


@dataclass
class Reservoir:
    survey: list
    crest_elevation: float
    spillway_width: float
    weir_coefficient: float
    outlet_area: float
    outlet_elevation: float
    outlet_coefficient: float


def surface_area(reservoir, elevation):
    """Linear interpolation in the surveyed (elevation, area) table."""
    survey = reservoir.survey
    if elevation <= survey[0][0]:
        return survey[0][1]
    for (z1, a1), (z2, a2) in zip(survey, survey[1:]):
        if z1 <= elevation <= z2:
            return a1 + (a2 - a1) * (elevation - z1) / (z2 - z1)
    return survey[-1][1]


def storage(reservoir, elevation, dz=0.01):
    """Stored volume (m3) below the given elevation."""
    bottom = reservoir.survey[0][0]
    volume = 0.0
    z = bottom
    while z < elevation:
        step = min(dz, elevation - z)
        volume += surface_area(reservoir, z + step / 2) * step
        z += step
    return volume


def outflow(reservoir, elevation):
    """Bottom outlet (orifice) plus ogee spillway (weir) discharge (m3/s)."""
    q = 0.0
    head = elevation - reservoir.outlet_elevation
    if head > 0:
        q += reservoir.outlet_coefficient * reservoir.outlet_area * math.sqrt(2 * GRAVITY * head)
    over_crest = elevation - reservoir.crest_elevation
    if over_crest > 0:
        q += reservoir.weir_coefficient * reservoir.spillway_width * over_crest ** 1.5
    return q


def solve_elevation(reservoir, target, dt, low, high, tolerance=1e-9):
    """Find the elevation where 2S/dt + O equals the target."""
    while high - low > tolerance:
        mid = (low + high) / 2
        if 2 * storage(reservoir, mid) / dt + outflow(reservoir, mid) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def route(reservoir, inflows, initial_elevation, dt=3600.0):
    bottom = reservoir.survey[0][0]
    top = reservoir.survey[-1][0]
    elevations = [initial_elevation]
    outflows = [outflow(reservoir, initial_elevation)]
    for i in range(1, len(inflows)):
        z = elevations[-1]
        target = (inflows[i - 1] + inflows[i]
                  + 2 * storage(reservoir, z) / dt - outflow(reservoir, z))
        z_new = solve_elevation(reservoir, target, dt, bottom, top)
        elevations.append(z_new)
        outflows.append(outflow(reservoir, z_new))
    return elevations, outflows


def summarise(inflows, elevations, outflows):
    peak_in = max(inflows)
    peak_out = max(outflows)
    return {
        "steps": len(inflows),
        "peak_inflow_m3s": round(peak_in, 3),
        "peak_outflow_m3s": round(peak_out, 3),
        "attenuation_pct": round(100 * (1 - peak_out / peak_in), 3),
        "max_elevation_m": round(max(elevations), 4),
        "peak_delay_h": outflows.index(peak_out) - inflows.index(peak_in),
    }
