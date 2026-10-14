"""WaterSim benchmark runner.

Usage:
    python main.py                 run all cases
    python main.py river sensors   run selected cases
    python main.py --list          list the available cases
"""

import argparse
import os
import sys
import time

from watersim import data, groundwater, pipe_network, reservoir, river, runoff, sensors, watershed

DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def case_pipes():
    network = data.build_grid_network(loops_x=7, loops_y=7)
    return pipe_network.analyse(network)


def case_river():
    reaches = data.build_river_reaches()
    discharges = data.daily_discharge(days=100)
    return river.summarise(river.analyse_reaches(reaches, discharges))


def case_groundwater():
    aquifer = groundwater.Aquifer(rows=120, cols=120)
    wells = [groundwater.Well(row=15 + 20 * (k // 5), col=15 + 20 * (k % 5), rate=400.0 + 25 * k)
             for k in range(25)]
    heads, days = groundwater.simulate(aquifer, wells, steps=300)
    return groundwater.summarise(aquifer, wells, heads, days)


def case_watershed():
    dem = data.build_dem(rows=100, cols=100)
    directions, accumulation = watershed.flow_accumulation(dem)
    return watershed.summarise(dem, directions, accumulation)


def case_runoff():
    rain = data.hourly_rainfall(hours=5 * 365 * 24)
    return runoff.simulate(rain)


def case_reservoir():
    res = data.build_reservoir()
    inflows = data.inflow_hydrograph(steps=96)
    elevations, outflows = reservoir.route(res, inflows, initial_elevation=118.0)
    return reservoir.summarise(inflows, elevations, outflows)


def case_sensors():
    stations_path, readings_path = data.write_sensor_files(DATA_FOLDER, stations=15, hours=30 * 24)
    totals, report = sensors.analyse(stations_path, readings_path)
    with open(os.path.join(DATA_FOLDER, "sensor_report.txt"), "w") as f:
        f.write(report)
    return totals


CASES = {
    "pipes": ("Drinking-water pipe network (Hardy Cross)", case_pipes),
    "river": ("River reach depths (Manning)", case_river),
    "groundwater": ("Groundwater flow with pumping wells", case_groundwater),
    "watershed": ("Watershed flow accumulation (D8)", case_watershed),
    "runoff": ("Rainfall-runoff (SCS-CN + unit hydrograph)", case_runoff),
    "reservoir": ("Reservoir flood routing (modified Puls)", case_reservoir),
    "sensors": ("Sensor log analysis", case_sensors),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the WaterSim cases and time them.")
    parser.add_argument("cases", nargs="*", help="cases to run (default: all)")
    parser.add_argument("--list", action="store_true", help="list available cases")
    args = parser.parse_args(argv)

    if args.list:
        for name, (description, _) in CASES.items():
            print(f"{name:12s} {description}")
        return 0

    selected = args.cases or list(CASES)
    unknown = [name for name in selected if name not in CASES]
    if unknown:
        parser.error(f"unknown case(s): {', '.join(unknown)}. Use --list to see the options.")

    timings = {}
    for name in selected:
        description, func = CASES[name]
        print(f"=== {name}: {description}", flush=True)
        start = time.perf_counter()
        result = func()
        timings[name] = time.perf_counter() - start
        for key, value in result.items():
            print(f"    {key:22s} {value}")
        print(f"    {'runtime':22s} {timings[name]:.2f} s", flush=True)

    print("\n=== Summary")
    for name, seconds in timings.items():
        print(f"    {name:12s} {seconds:8.2f} s")
    print(f"    {'TOTAL':12s} {sum(timings.values()):8.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
