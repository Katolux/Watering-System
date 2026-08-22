"""Build and serve the isolated GardenHub demo database."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
from gardenhub.db.connection import DEMO_DB_PATH  # noqa: E402

DEMO_DB = DEMO_DB_PATH.resolve()
os.environ["GARDENHUB_DB_PATH"] = str(DEMO_DB)

from gardenhub.db.connection import get_conn, get_db_path  # noqa: E402
from gardenhub.db.initialization import init_all_tables  # noqa: E402
from seeding.plant_seeder import seed_all_plants  # noqa: E402


def _assert_demo_target() -> None:
    if get_db_path() != DEMO_DB_PATH.resolve() or get_db_path() != DEMO_DB:
        raise RuntimeError(f"Refusing demo operation for non-demo database: {get_db_path()}")


def _timestamp(day: date, hour: int, minute: int = 0) -> str:
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc).isoformat()


def _clear_demo_records(cur) -> None:
    for table in (
        "sensor_readings", "watering_events", "watering_decisions",
        "system_events", "bed_plantings", "sensors", "beds", "zones",
        "plant_companions", "plant_varieties", "plants", "weather_data",
    ):
        cur.execute(f"DELETE FROM {table}")


def _seed_operational_data() -> None:
    today = date.today()
    zones = [
        ("raised-zone", "Raised beds", 1),
        ("greenhouse-zone", "Greenhouse", 1),
        ("patio-zone", "Patio and containers", 1),
    ]
    beds = [
        ("raised-1", "raised-zone", 1), ("raised-2", "raised-zone", 1),
        ("raised-3", "raised-zone", 1), ("greenhouse", "greenhouse-zone", 1),
        ("patio-herbs", "patio-zone", 1), ("resting-bed", "raised-zone", 0),
    ]
    plantings = [
        ("raised-1", "tomato", "san_marzano", 8, "Demo tomatoes"),
        ("raised-1", "basil", None, 6, "Demo companion planting"),
        ("raised-2", "lettuce", None, 12, "Demo succession bed"),
        ("raised-2", "carrot", None, 18, "Demo succession bed"),
        ("raised-3", "cucumber", None, 6, "Demo trellis row"),
        ("raised-3", "marigold", None, 4, "Demo border planting"),
        ("greenhouse", "pepper", None, 8, "Demo greenhouse crop"),
        ("greenhouse", "tomato", "sweet_orange_f1", 4, "Demo greenhouse crop"),
        ("patio-herbs", "strawberry", None, 10, "Demo container crop"),
    ]
    sensors = [
        ("demo-moisture-01", "raised-1", "moisture", 15, 1),
        ("demo-moisture-02", "raised-2", "moisture", 15, 1),
        ("demo-moisture-03", "raised-3", "moisture", 15, 0),
        ("demo-moisture-04", "greenhouse", "moisture", 20, 1),
        ("demo-moisture-05", "patio-herbs", "moisture", 12, 1),
        ("demo-moisture-06", "resting-bed", "moisture", 15, 0),
    ]

    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany("INSERT INTO zones (zone_id, name, active) VALUES (?, ?, ?)", zones)
        cur.executemany("INSERT INTO beds (bed_id, zone_id, active) VALUES (?, ?, ?)", beds)
        cur.executemany(
            """INSERT INTO bed_plantings
               (bed_id, plant_id, variety_id, quantity, planted_at, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(b, p, v, q, _timestamp(today - timedelta(days=42 + i), 9), n)
             for i, (b, p, v, q, n) in enumerate(plantings)],
        )
        cur.executemany(
            "INSERT INTO sensors (sensor_id, bed_id, sensor_type, depth_cm, active) VALUES (?, ?, ?, ?, ?)",
            sensors,
        )

        reading_rows = []
        reading_sensors = sensors[:5]
        for day_offset in range(7, 0, -1):
            reading_date = today - timedelta(days=day_offset)
            for sensor_index, sensor in enumerate(reading_sensors):
                for slot in (1, 2):
                    moisture = 43 + ((day_offset * 5 + sensor_index * 7 + slot * 3) % 31)
                    raw = 820 - moisture * 6
                    reading_rows.append((_timestamp(reading_date, 8 + slot * 5), reading_date.isoformat(), sensor[1], sensor[0], slot, raw, moisture))
        for sensor_index, sensor in enumerate(reading_sensors):
            for slot in range(1, 7):
                moisture = 46 + ((sensor_index * 9 + slot * 4) % 28)
                raw = 820 - moisture * 6
                reading_rows.append((_timestamp(today, 5 + slot * 2), today.isoformat(), sensor[1], sensor[0], slot, raw, moisture))
        cur.executemany(
            """INSERT INTO sensor_readings
               (timestamp, date, bed_id, sensor_id, slot, moisture_raw, moisture_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            reading_rows,
        )

        weather_rows = []
        for offset in range(13, -1, -1):
            record_date = today - timedelta(days=offset)
            temp_max = 20.0 + ((13 - offset) % 6) * 1.4
            temp_min = temp_max - 8.2
            rain = (0.0, 1.8, 0.0, 6.4, 0.0, 0.0, 3.2)[offset % 7]
            weather_rows.append((record_date.isoformat(), _timestamp(record_date, 22), temp_max, temp_min, rain, 330 + offset * 8, 910, 8 + offset % 5, 185 + offset * 7))
        cur.executemany(
            """INSERT INTO weather_data
               (date, timestamp, temp_max, temp_min, precipitation, sunshine, daylight, wind_max, wind_dir)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            weather_rows,
        )

        bed_names = ["raised-1", "raised-2", "raised-3", "greenhouse", "patio-herbs"]
        for bed_index, bed_id in enumerate(bed_names):
            for decision_index, day_offset in enumerate((2, 0)):
                decision_day = today - timedelta(days=day_offset)
                final_minutes = 12 + bed_index * 3 + decision_index * 2
                cur.execute(
                    """INSERT INTO watering_decisions
                       (timestamp, date, bed_id, plant_name, avg_moisture, temp_max, precipitation,
                        base_minutes, final_minutes, soil_factor, temp_factor, rain_factor)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (_timestamp(decision_day, 6, bed_index * 4), decision_day.isoformat(), bed_id,
                     "Demo planting group", 48 + bed_index * 4, 24.2, 0.0, 30,
                     final_minutes, 0.8 + bed_index * 0.08, 1.05, 1.0),
                )

        for index in range(12):
            event_day = today - timedelta(days=index // 3)
            bed_id = bed_names[index % len(bed_names)]
            cur.execute(
                """INSERT INTO watering_events
                   (timestamp, date, bed_id, minutes, mode, soil_factor, temp_factor, rain_factor, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (_timestamp(event_day, 6 + index % 3, index * 3), event_day.isoformat(), bed_id,
                 10 + (index % 5) * 3, "demo", 1.0, 1.05, 1.0,
                 "Deterministic demo watering record"),
            )

        event_specs = [
            ("WARNING", "sensor", "Inactive demo sensor requires review", "raised-3"),
            ("WARNING", "watering_engine", "Demo bed moisture is below its configured range", "raised-1"),
            ("WARNING", "weather", "Demo rainfall record changed a watering decision", None),
            ("INFO", "watering", "Demo watering event recorded", "greenhouse"),
            ("INFO", "sensor", "Demo moisture samples imported", "raised-2"),
            ("INFO", "catalog", "Demo plant catalogue seeded", None),
            ("INFO", "watering_engine", "Demo decisions recalculated", None),
            ("INFO", "sensor", "Demo sensor assigned", "patio-herbs"),
            ("INFO", "garden", "Demo bed assignment updated", "raised-3"),
            ("INFO", "weather", "Demo weather history loaded", None),
            ("INFO", "watering", "Demo manual watering record stored", "raised-2"),
            ("INFO", "system", "GardenHub demo dataset ready", None),
        ]
        for index, (level, source, message, bed_id) in enumerate(event_specs):
            event_day = today - timedelta(days=index // 4)
            cur.execute(
                """INSERT INTO system_events
                   (timestamp, date, level, source, bed_id, message, details)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (_timestamp(event_day, 15 - index % 4, index * 2), event_day.isoformat(), level,
                 source, bed_id, message, json.dumps({"data_status": "demo"})),
            )
        conn.commit()


def seed() -> None:
    _assert_demo_target()
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    init_all_tables()
    with get_conn() as conn:
        _clear_demo_records(conn.cursor())
        conn.commit()
    print(f"Using demo database: {DEMO_DB}")
    seed_all_plants(BASE_DIR / "plants")
    _seed_operational_data()
    print("Demo seed complete: 52 plants, 25 varieties, 205 companion relationships, 3 zones, 6 beds, 9 plantings, 6 sensors, 100 readings, 10 decisions, 12 watering events, 14 weather records, 12 system events.")


def reset() -> None:
    _assert_demo_target()
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    print(f"Confirmed isolated demo target: {DEMO_DB}")
    if DEMO_DB.exists():
        try:
            DEMO_DB.unlink()
        except PermissionError as exc:
            raise SystemExit("Cannot reset while the demo database is in use. Stop the demo server and run reset again.") from exc
        print("Removed previous demo database.")
    seed()


def serve() -> None:
    _assert_demo_target()
    if not DEMO_DB.exists():
        raise SystemExit("Demo database is missing. Run: python -m gardenhub.seeding.demo reset")
    print(f"Serving GardenHub with demo database: {DEMO_DB}")
    from app import app
    app.run(host="0.0.0.0", port=5000, debug=False)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("reset", "seed", "serve"))
    args = parser.parse_args(argv)
    {"reset": reset, "seed": seed, "serve": serve}[args.command]()


if __name__ == "__main__":
    main(sys.argv[1:])
