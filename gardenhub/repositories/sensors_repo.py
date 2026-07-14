from datetime import date, datetime, timezone

from gardenhub.db.connection import get_conn


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


def add_sensor(sensor_id, active=True, bed_id="unassigned"):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO zones (zone_id, name, active)
            VALUES (?, ?, ?)
            """,
            ("default", "Default zone", 1)
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO beds (bed_id, zone_id, active)
            VALUES (?, ?, ?)
            """,
            (bed_id, "default", 0)
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO sensors (sensor_id, bed_id, active)
            VALUES (?, ?, ?)
            """,
            (sensor_id, bed_id, 1 if active else 0)
        )

        conn.commit()


def assign_sensor_to_bed(sensor_id, bed_id):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM beds WHERE bed_id = ?", (bed_id,))
        if cur.fetchone() is None:
            return False

        cur.execute("SELECT 1 FROM sensors WHERE sensor_id = ?", (sensor_id,))
        if cur.fetchone() is None:
            return False

        cur.execute(
            """
            UPDATE sensors
            SET bed_id = ?
            WHERE sensor_id = ?
            """,
            (bed_id, sensor_id)
        )

        conn.commit()
        return cur.rowcount > 0


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
