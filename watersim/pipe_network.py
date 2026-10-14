"""Steady-state flow in a looped pipe network (Hardy Cross method).

Head losses use Darcy-Weisbach with the Colebrook-White friction factor.
"""

import copy
import math
from dataclasses import dataclass, field

GRAVITY = 9.81
KINEMATIC_VISCOSITY = 1.004e-6


@dataclass
class Pipe:
    id: str
    start: int
    end: int
    length: float
    diameter: float
    roughness: float
    flow: float = 0.0


@dataclass
class Network:
    nodes: dict
    pipes: list
    loops: list = field(default_factory=list)


def find_pipe(pipes, pipe_id):
    for pipe in pipes:
        if pipe.id == pipe_id:
            return pipe
    raise KeyError(pipe_id)


def colebrook(reynolds, relative_roughness):
    """Solve the Colebrook-White equation for the Darcy friction factor."""
    def residual(f):
        return 1.0 / math.sqrt(f) + 2.0 * math.log10(
            relative_roughness / 3.7 + 2.51 / (reynolds * math.sqrt(f)))

    step = 0.00001
    f_low = 0.005
    r_low = residual(f_low)
    while f_low < 0.2:
        f_high = f_low + step
        r_high = residual(f_high)
        if r_low * r_high <= 0:
            return f_low + step * r_low / (r_low - r_high)
        f_low, r_low = f_high, r_high
    return f_low


def friction_factor(reynolds, relative_roughness):
    """Darcy friction factor: laminar below Re 2000, Colebrook-White above 4000,
    linear interpolation in the transition zone."""
    if reynolds < 1e-9:
        return 0.0
    if reynolds < 2000:
        return 64.0 / reynolds
    if reynolds < 4000:
        f_laminar = 64.0 / 2000
        f_turbulent = colebrook(4000, relative_roughness)
        return f_laminar + (f_turbulent - f_laminar) * (reynolds - 2000) / 2000
    return colebrook(reynolds, relative_roughness)


def head_loss(pipe, flow):
    """Signed Darcy-Weisbach head loss (m) for the given flow (m3/s)."""
    area = math.pi * pipe.diameter ** 2 / 4
    velocity = abs(flow) / area
    reynolds = velocity * pipe.diameter / KINEMATIC_VISCOSITY
    f = friction_factor(reynolds, pipe.roughness / pipe.diameter)
    loss = f * (pipe.length / pipe.diameter) * velocity ** 2 / (2 * GRAVITY)
    return math.copysign(loss, flow)


def solve_hardy_cross(network, tolerance=1e-7, max_iterations=1000):
    """Balance the loop flows in place; returns the number of iterations used."""
    for iteration in range(1, max_iterations + 1):
        previous = copy.deepcopy(network.pipes)

        for loop in network.loops:
            sum_h = 0.0
            sum_dh = 0.0
            for pipe_id, direction in loop:
                pipe = find_pipe(network.pipes, pipe_id)
                q = direction * pipe.flow
                h = head_loss(pipe, q)
                sum_h += h
                if q != 0:
                    sum_dh += 2 * h / q
            if sum_dh == 0:
                continue
            correction = -sum_h / sum_dh
            for pipe_id, direction in loop:
                pipe = find_pipe(network.pipes, pipe_id)
                pipe.flow += direction * correction

        change = 0.0
        for pipe in network.pipes:
            old = find_pipe(previous, pipe.id)
            change = max(change, abs(pipe.flow - old.flow))
        if change < tolerance:
            return iteration
    return max_iterations


def node_heads(network, source_node=0, source_head=60.0):
    """Hydraulic head at each node, walking outward from the source."""
    heads = {source_node: source_head}
    queue = [source_node]
    while queue:
        node = queue.pop(0)
        for pipe in network.pipes:
            if pipe.start == node and pipe.end not in heads:
                heads[pipe.end] = heads[node] - head_loss(pipe, pipe.flow)
                queue.append(pipe.end)
            elif pipe.end == node and pipe.start not in heads:
                heads[pipe.start] = heads[node] + head_loss(pipe, pipe.flow)
                queue.append(pipe.start)
    return heads


def continuity_error(network):
    """Largest node imbalance (m3/s): inflow - outflow - demand."""
    worst = 0.0
    for node, demand in network.nodes.items():
        balance = 0.0
        for pipe in network.pipes:
            if pipe.end == node:
                balance += pipe.flow
            if pipe.start == node:
                balance -= pipe.flow
        worst = max(worst, abs(balance - demand))
    return worst


def analyse(network):
    iterations = solve_hardy_cross(network)
    heads = node_heads(network)
    velocities = [abs(p.flow) / (math.pi * p.diameter ** 2 / 4) for p in network.pipes]
    return {
        "iterations": iterations,
        "min_head_m": round(min(heads.values()), 4),
        "max_velocity_ms": round(max(velocities), 4),
        "total_supply_m3s": round(-network.nodes[0], 6),
        "continuity_error": continuity_error(network),
    }
