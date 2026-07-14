from datetime import datetime, timezone

from gardenhub.db.connection import get_conn


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
