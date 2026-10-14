from datetime import datetime

import pytest

from watersim import data, sensors


@pytest.fixture(scope="module")
def sensor_files(tmp_path_factory):
    folder = tmp_path_factory.mktemp("sensors")
    return data.write_sensor_files(str(folder), stations=4, hours=120)


def reading(hour, level=2.0, station="ST000"):
    return sensors.Reading(station, datetime(2026, 1, 1, hour), level, 10.0 * level)


def test_load_readings_filters_station(sensor_files):
    _, readings_path = sensor_files
    readings = sensors.load_readings(readings_path, "ST002")
    assert len(readings) >= 120
    assert all(r.station_id == "ST002" for r in readings)
    assert isinstance(readings[0].timestamp, datetime)


def test_remove_duplicates_keeps_first_occurrence_order():
    a, b, c = reading(1), reading(2), reading(3)
    assert sensors.remove_duplicates([a, b, a, c, b]) == [a, b, c]


def test_detect_anomalies_flags_spike():
    readings = [reading(h % 24, 2.0 + 0.01 * (h % 5)) for h in range(60)]
    spike = reading(5, 9.0)
    readings.append(spike)
    assert sensors.detect_anomalies(readings) == [spike]


def test_daily_mean_flow():
    readings = [
        sensors.Reading("ST000", datetime(2026, 1, 1, 1), 1.0, 10.0),
        sensors.Reading("ST000", datetime(2026, 1, 1, 2), 1.0, 20.0),
        sensors.Reading("ST000", datetime(2026, 1, 2, 1), 1.0, 40.0),
    ]
    result = sensors.daily_mean_flow(readings)
    assert list(result.values()) == pytest.approx([15.0, 40.0])


def test_reference_results(sensor_files):
    stations_path, readings_path = sensor_files
    totals, report = sensors.analyse(stations_path, readings_path)
    assert totals == {
        "stations": 4,
        "readings": 480,
        "duplicates": 1,
        "anomalies": 5,
        "alarm_hours": 91,
        "max_daily_flow": pytest.approx(204.9171, abs=1e-4),
    }
    assert report.count("ST00") == 4
    assert "2026-01-05" in report
