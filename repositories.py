from datetime import datetime, timezone, date, timedelta
from db import get_conn
from calibration import raw_to_pct



# -----------------------------
# BEDS
# -----------------------------

def add_bed(bed_id, active=True):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO beds (bed_id, active)
            VALUES (?, ?)
            """,
            (bed_id, 1 if active else 0)
        )


def get_all_beds():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT bed_id, active FROM beds")
        rows = cur.fetchall()
    return rows


def list_beds_with_sensors():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT bed_id, active FROM beds")
        beds = cur.fetchall()

        cur.execute("SELECT sensor_id, bed_id, active FROM sensors")
        sensors = cur.fetchall()

    if not beds:
        print("No beds found.")
        return

    print("\nBeds and sensors:")
    for bed_id, bed_active in beds:
        bed_status = "ACTIVE" if bed_active else "INACTIVE"
        print(f"\n{bed_id} [{bed_status}]")

        found = False
        for sensor_id, sensor_bed_id, sensor_active in sensors:
            if sensor_bed_id == bed_id:
                sensor_status = "ACTIVE" if sensor_active else "INACTIVE"
                print(f"  - {sensor_id} [{sensor_status}]")
                found = True

        if not found:
            print("  (no sensors)")


# -----------------------------
# PLANTS
# -----------------------------

def add_plant(plant_id, name, min_moisture, max_moisture, base_minutes):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO plants
            (plant_id, name, min_moisture, max_moisture, base_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (plant_id, name, min_moisture, max_moisture, base_minutes)
        )


def get_all_plants():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT plant_id, name, min_moisture, max_moisture, base_minutes FROM plants"
        )
        rows = cur.fetchall()
    return rows


def assign_plant_to_bed(bed_id, plant_id, plant_name, quantity=1):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bed_plantings
            (bed_id, plant_id, plant_name, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (bed_id, plant_id, plant_name, quantity)
        )


def get_beds_with_plants():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                beds.bed_id,
                beds.active,
                plants.name,
                plants.min_moisture,
                plants.max_moisture,
                plants.base_minutes
            FROM beds
            LEFT JOIN bed_plantings bp ON beds.bed_id = bp.bed_id
            LEFT JOIN plants ON bp.plant_id = plants.plant_id
            """
        )
        rows = cur.fetchall()
    return rows


# -----------------------------
# SENSORS
# -----------------------------

def get_all_sensors():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT sensor_id, bed_id, active
            FROM sensors
            ORDER BY sensor_id
            """
        )
        rows = cur.fetchall()
    return rows


def add_sensor(sensor_id, active=True):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO sensors (sensor_id, active)
            VALUES (?, ?)
            """,
            (sensor_id, 1 if active else 0)
        )


def assign_sensor_to_bed(sensor_id, bed_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sensors
            SET bed_id = ?
            WHERE sensor_id = ?
            """,
            (bed_id, sensor_id)
        )


# -----------------------------
# SENSOR READINGS
# -----------------------------

def next_slot_for_today(bed_id):
    today = date.today().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM sensor_readings
            WHERE bed_id = ? AND date = ?
            """,
            (bed_id, today)
        )
        next_slot = cur.fetchone()[0] + 1

    if next_slot > 6:
        return None
    return next_slot



def save_reading(bed_id, sensor_id, slot, moisture_raw):
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sensor_readings (
                timestamp,
                date,
                bed_id,
                sensor_id,
                slot,
                moisture_raw
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                now.isoformat(),
                now.date().isoformat(),
                bed_id,
                sensor_id,
                slot,
                moisture_raw
            )
        )


def get_today_moisture_slots():
    today = date.today().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bed_id, slot, moisture_raw
            FROM sensor_readings
            WHERE date = ?
            """,
            (today,)
        )
        rows = cur.fetchall()

    result = {}
    for bed_id, slot, moisture in rows:
        result.setdefault(bed_id, {})[slot] = {
            "raw": moisture,
            "pct": raw_to_pct(moisture)
        }

    return result



# -----------------------------
# WEATHER
# -----------------------------

def get_latest_weather_date():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM weather_data")
        row = cur.fetchone()
    return row[0]


def should_refresh_weather():
    try:
        latest = get_latest_weather_date()
    except Exception:
        return True

    if latest is None:
        return True

    latest_date = date.fromisoformat(latest)
    return (date.today() - latest_date) >= timedelta(days=3)


# -----------------------------
# WATERING
# -----------------------------

def save_watering_decision(
    bed_id,
    plant_name,
    avg_moisture,
    temp_max,
    precipitation,
    base_minutes,
    final_minutes,
    soil_factor,
    temp_factor,
    rain_factor
):
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO watering_decisions (
                timestamp,
                date,
                bed_id,
                plant_name,
                avg_moisture,
                temp_max,
                precipitation,
                base_minutes,
                final_minutes,
                soil_factor,
                temp_factor,
                rain_factor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.isoformat(),
                now.date().isoformat(),
                bed_id,
                plant_name,
                avg_moisture,
                temp_max,
                precipitation,
                base_minutes,
                final_minutes,
                soil_factor,
                temp_factor,
                rain_factor
            )
        )


def get_latest_watering_decision(bed_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                final_minutes,
                soil_factor,
                temp_factor,
                rain_factor,
                timestamp
            FROM watering_decisions
            WHERE bed_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (bed_id,)
        )
        row = cur.fetchone()
    return row


def log_watering_event(
    bed_id,
    minutes,
    mode="manual",
    soil_factor=None,
    temp_factor=None,
    rain_factor=None,
    source_decision_id=None,
    note=None
):
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO watering_events (
                timestamp,
                date,
                bed_id,
                minutes,
                mode,
                soil_factor,
                temp_factor,
                rain_factor,
                source_decision_id,
                note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.isoformat(),
                now.date().isoformat(),
                bed_id,
                minutes,
                mode,
                soil_factor,
                temp_factor,
                rain_factor,
                source_decision_id,
                note
            )
        )
