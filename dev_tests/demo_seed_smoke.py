"""Smoke-test the deterministic demo seed without touching the default database."""

import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_DB = ROOT / "dev_data" / "gardenhub_demo.db"
PRODUCTION_DB = ROOT / "garden_system.db"
TABLES = (
    "plants", "plant_varieties", "plant_companions", "zones", "beds",
    "bed_plantings", "sensors", "sensor_readings", "watering_decisions",
    "watering_events", "weather_data", "system_events",
)
EXPECTED = {
    "plants": 52,
    "plant_varieties": 25,
    "plant_companions": 205,
    "zones": 3,
    "beds": 6,
    "bed_plantings": 9,
    "sensors": 6,
    "sensor_readings": 100,
    "watering_decisions": 10,
    "watering_events": 12,
    "weather_data": 14,
    "system_events": 12,
}


def counts(path):
    with sqlite3.connect(path) as conn:
        return {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}


def run(command):
    return subprocess.run(
        [sys.executable, "-m", "gardenhub.seeding.demo", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def main():
    production_before = counts(PRODUCTION_DB)
    reset_output = run("reset")
    assert counts(DEMO_DB) == EXPECTED
    run("seed")
    assert counts(DEMO_DB) == EXPECTED
    with sqlite3.connect(DEMO_DB) as conn:
        assert conn.execute("SELECT MAX(date) FROM weather_data").fetchone()[0] == date.today().isoformat()
        assert conn.execute("SELECT COUNT(*) FROM system_events WHERE level = 'WARNING'").fetchone()[0] == 3
    assert counts(PRODUCTION_DB) == production_before
    print("Demo seed smoke test passed; production counts are unchanged.")


if __name__ == "__main__":
    main()
