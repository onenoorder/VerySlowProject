"""Open channel flow in trapezoidal river reaches (Manning's equation)."""

import math
from dataclasses import dataclass

GRAVITY = 9.81


@dataclass
class Channel:
    name: str
    bottom_width: float
    side_slope: float
    manning_n: float
    bed_slope: float


def flow_area(channel, depth):
    return (channel.bottom_width + channel.side_slope * depth) * depth


def wetted_perimeter(channel, depth):
    return channel.bottom_width + 2 * depth * math.sqrt(1 + channel.side_slope ** 2)


def top_width(channel, depth):
    return channel.bottom_width + 2 * channel.side_slope * depth


def manning_discharge(channel, depth):
    area = flow_area(channel, depth)
    radius = area / wetted_perimeter(channel, depth)
    return area * radius ** (2 / 3) * math.sqrt(channel.bed_slope) / channel.manning_n


def normal_depth(channel, discharge, step=0.0001):
    depth = step
    while manning_discharge(channel, depth) < discharge:
        depth += step
    return depth


def critical_depth(channel, discharge, step=0.0001):
    depth = step
    while discharge ** 2 * top_width(channel, depth) / (GRAVITY * flow_area(channel, depth) ** 3) > 1:
        depth += step
    return depth


def froude_number(channel, discharge, depth):
    area = flow_area(channel, depth)
    hydraulic_depth = area / top_width(channel, depth)
    return (discharge / area) / math.sqrt(GRAVITY * hydraulic_depth)


def analyse_reaches(reaches, discharges):
    """Daily depth, velocity and flow regime for every reach."""
    results = []
    for day, q in enumerate(discharges):
        for reach in reaches:
            yn = normal_depth(reach, q)
            yc = critical_depth(reach, q)
            fr = froude_number(reach, q, yn)
            results.append({
                "day": day,
                "reach": reach.name,
                "discharge": q,
                "normal_depth": yn,
                "critical_depth": yc,
                "velocity": q / flow_area(reach, yn),
                "froude": fr,
                "regime": "supercritical" if fr > 1 else "subcritical",
            })
    return results


def summarise(results):
    flood_days = []
    for r in results:
        if r["normal_depth"] > 4.0 and r["day"] not in flood_days:
            flood_days.append(r["day"])
    return {
        "rows": len(results),
        "max_depth_m": round(max(r["normal_depth"] for r in results), 4),
        "max_velocity_ms": round(max(r["velocity"] for r in results), 4),
        "supercritical_rows": sum(1 for r in results if r["regime"] == "supercritical"),
        "flood_days": len(flood_days),
    }
