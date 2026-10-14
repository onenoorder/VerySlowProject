"""Analysis of water level and discharge sensor logs."""

import csv
import statistics
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reading:
    station_id: str
    timestamp: datetime
    water_level: float
    flow: float


@dataclass
class Station:
    station_id: str
    name: str
    river: str
    alarm_level: float


def load_stations(path):
    stations = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            stations.append(Station(row["station_id"], row["name"], row["river"],
                                    float(row["alarm_level_m"])))
    return stations


def load_readings(path, station_id):
    readings = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            reading = Reading(
                station_id=row["station_id"],
                timestamp=datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S"),
                water_level=float(row["water_level_m"]),
                flow=float(row["flow_m3s"]),
            )
            if reading.station_id == station_id:
                readings.append(reading)
    return readings


def remove_duplicates(readings):
    unique = []
    for reading in readings:
        if reading not in unique:
            unique.append(reading)
    return unique


def detect_anomalies(readings, z_limit=4.0):
    anomalies = []
    for reading in readings:
        levels = [r.water_level for r in readings]
        mean = statistics.mean(levels)
        stdev = statistics.stdev(levels)
        if abs(reading.water_level - mean) > z_limit * stdev:
            anomalies.append(reading)
    return anomalies


def daily_mean_flow(readings):
    days = sorted(set(r.timestamp.date() for r in readings))
    result = {}
    for day in days:
        flows = [r.flow for r in readings if r.timestamp.date() == day]
        result[day] = statistics.mean(flows)
    return result


def analyse(stations_path, readings_path):
    stations = load_stations(stations_path)
    report = ""
    totals = {"stations": 0, "readings": 0, "duplicates": 0, "anomalies": 0,
              "alarm_hours": 0, "max_daily_flow": 0.0}
    for station in stations:
        raw = load_readings(readings_path, station.station_id)
        readings = remove_duplicates(raw)
        readings.sort(key=lambda r: r.timestamp)
        anomalies = detect_anomalies(readings)
        daily = daily_mean_flow(readings)
        alarm_hours = sum(1 for r in readings
                          if r.water_level > station.alarm_level and r not in anomalies)

        report += f"{station.station_id} {station.name} ({station.river})\n"
        report += f"  readings: {len(readings)}  duplicates: {len(raw) - len(readings)}\n"
        report += f"  anomalies: {len(anomalies)}  alarm hours: {alarm_hours}\n"
        for day, q in daily.items():
            report += f"  {day}: {q:.2f} m3/s\n"

        totals["stations"] += 1
        totals["readings"] += len(readings)
        totals["duplicates"] += len(raw) - len(readings)
        totals["anomalies"] += len(anomalies)
        totals["alarm_hours"] += alarm_hours
        totals["max_daily_flow"] = max(totals["max_daily_flow"], max(daily.values()))
    totals["max_daily_flow"] = round(totals["max_daily_flow"], 4)
    return totals, report
