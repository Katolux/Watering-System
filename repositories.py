from datetime import datetime, timezone, date, timedelta
from db import get_conn
from calibration import raw_to_pct
import json




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


def assign_plant_to_bed(bed_id, plant_id, variety_id=None, quantity=1, planted_at=None, notes=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bed_plantings
            (bed_id, plant_id, variety_id, quantity, planted_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (bed_id, plant_id, variety_id, quantity, planted_at, notes)
        )
        conn.commit()

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
            LEFT JOIN bed_plantings bp
                ON beds.bed_id = bp.bed_id
               AND bp.removed_at IS NULL
            LEFT JOIN plants
                ON bp.plant_id = plants.plant_id
            """
        )
        rows = cur.fetchall()
    return rows

def get_all_plants_catalog():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                plant_id,
                name,
                category,
                family,
                emoji,
                water_need_overall,
                calendar_json
            FROM plants
            ORDER BY name COLLATE NOCASE
        """)
        return cur.fetchall()

def get_plant_by_id(plant_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                plant_id,
                name,
                scientific_name,
                category,
                family,
                icon_key,
                emoji,
                photo_key,
                spacing_in_row_cm,
                spacing_between_rows_cm,
                root_depth_min_cm,
                root_depth_max_cm,
                root_type,
                water_need_overall,
                irrigation_sensitivity,
                mulch_helpful,
                min_moisture,
                max_moisture,
                base_minutes,
                soil_json,
                calendar_json,
                nutrition_json,
                care_json,
                plant_json,
                schema_version
            FROM plants
            WHERE plant_id = ?
        """, (plant_id,))
        return cur.fetchone()

def get_plant_varieties(plant_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT variety_id, name, notes
            FROM plant_varieties
            WHERE plant_id = ?
            ORDER BY name COLLATE NOCASE
        """, (plant_id,))
        return cur.fetchall()

def get_plant_companions(plant_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT other_plant_id, relation, reason, confidence, mechanism
            FROM plant_companions
            WHERE plant_id = ?
            ORDER BY relation, other_plant_id
        """, (plant_id,))
        return cur.fetchall()
    

def plant_exists(plant_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM plants WHERE plant_id = ?",
            (plant_id,)
        )
        return cur.fetchone() is not None
    

def variety_exists(plant_id, variety_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM plant_varieties
            WHERE plant_id = ? AND variety_id = ?
            """,
            (plant_id, variety_id)
        )
        return cur.fetchone() is not None
    

def insert_rich_plant(plant_data):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO plants (
                plant_id,
                name,
                scientific_name,
                category,
                family,
                icon_key,
                emoji,
                photo_key,
                spacing_in_row_cm,
                spacing_between_rows_cm,
                root_depth_min_cm,
                root_depth_max_cm,
                root_type,
                water_need_overall,
                irrigation_sensitivity,
                mulch_helpful,
                min_moisture,
                max_moisture,
                base_minutes,
                soil_json,
                calendar_json,
                nutrition_json,
                care_json,
                plant_json,
                schema_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plant_data["plant_id"],
            plant_data["name"],
            plant_data.get("scientific_name"),
            plant_data.get("category"),
            plant_data.get("family"),
            plant_data.get("icon_key"),
            plant_data.get("emoji"),
            plant_data.get("photo_key"),
            plant_data.get("spacing_in_row_cm"),
            plant_data.get("spacing_between_rows_cm"),
            plant_data.get("root_depth_min_cm"),
            plant_data.get("root_depth_max_cm"),
            plant_data.get("root_type"),
            plant_data.get("water_need_overall"),
            plant_data.get("irrigation_sensitivity"),
            1 if plant_data.get("mulch_helpful") else 0,
            plant_data.get("min_moisture"),
            plant_data.get("max_moisture"),
            plant_data.get("base_minutes"),
            json.dumps(plant_data.get("soil_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("calendar_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("nutrition_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("care_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("plant_json", {}), ensure_ascii=False),
            plant_data.get("schema_version", 1),
        ))

        conn.commit()


def insert_rich_variety(plant_id, variety_id, name, notes, overrides):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO plant_varieties (
                plant_id,
                variety_id,
                name,
                notes,
                overrides_json,
                resolved_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            plant_id,
            variety_id,
            name,
            notes,
            json.dumps(overrides, ensure_ascii=False),
            json.dumps(overrides, ensure_ascii=False)
        ))
        conn.commit()

def update_rich_plant(plant_id, plant_data):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE plants
            SET
                name = ?,
                scientific_name = ?,
                category = ?,
                family = ?,
                icon_key = ?,
                emoji = ?,
                photo_key = ?,
                spacing_in_row_cm = ?,
                spacing_between_rows_cm = ?,
                root_depth_min_cm = ?,
                root_depth_max_cm = ?,
                root_type = ?,
                water_need_overall = ?,
                irrigation_sensitivity = ?,
                mulch_helpful = ?,
                min_moisture = ?,
                max_moisture = ?,
                base_minutes = ?,
                soil_json = ?,
                calendar_json = ?,
                nutrition_json = ?,
                care_json = ?,
                plant_json = ?,
                schema_version = ?
            WHERE plant_id = ?
        """, (
            plant_data["name"],
            plant_data.get("scientific_name"),
            plant_data.get("category"),
            plant_data.get("family"),
            plant_data.get("icon_key"),
            plant_data.get("emoji"),
            plant_data.get("photo_key"),
            plant_data.get("spacing_in_row_cm"),
            plant_data.get("spacing_between_rows_cm"),
            plant_data.get("root_depth_min_cm"),
            plant_data.get("root_depth_max_cm"),
            plant_data.get("root_type"),
            plant_data.get("water_need_overall"),
            plant_data.get("irrigation_sensitivity"),
            1 if plant_data.get("mulch_helpful") else 0,
            plant_data.get("min_moisture"),
            plant_data.get("max_moisture"),
            plant_data.get("base_minutes"),
            json.dumps(plant_data.get("soil_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("calendar_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("nutrition_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("care_json", {}), ensure_ascii=False),
            json.dumps(plant_data.get("plant_json", {}), ensure_ascii=False),
            plant_data.get("schema_version", 1),
            plant_id
        ))

        conn.commit()

def delete_plant(plant_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM plant_companions WHERE plant_id = ?", (plant_id,))
        cur.execute("DELETE FROM plant_varieties WHERE plant_id = ?", (plant_id,))
        cur.execute("DELETE FROM bed_plantings WHERE plant_id = ?", (plant_id,))
        cur.execute("DELETE FROM plants WHERE plant_id = ?", (plant_id,))
        conn.commit()

def delete_variety(plant_id, variety_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM plant_varieties
            WHERE plant_id = ? AND variety_id = ?
            """,
            (plant_id, variety_id)
        )
        conn.commit()



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



def save_reading(bed_id, sensor_id, slot, moisture_raw, moisture_pct):
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
                moisture_raw,
                moisture_pct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.isoformat(),
                now.date().isoformat(),
                bed_id,
                sensor_id,
                slot,
                moisture_raw,
                moisture_pct
            )
        )


def get_today_moisture_slots():
    today = date.today().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bed_id, slot, moisture_raw, moisture_pct
            FROM sensor_readings
            WHERE date = ?
            """,
            (today,)
        )
        rows = cur.fetchall()

    result = {}
    for bed_id, slot, moisture_raw, moisture_pct in rows:
        result.setdefault(bed_id, {})[slot] = {
            "raw": moisture_raw,
            "pct": moisture_pct
        }

    return result

def get_recent_sensor_readings(limit=200):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, date, bed_id, sensor_id, slot, moisture_raw, moisture_pct
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()



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

def get_recent_watering_events(limit=100):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, bed_id, minutes, mode, source_decision_id, note
            FROM watering_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()

