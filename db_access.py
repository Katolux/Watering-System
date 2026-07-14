from datetime import date
from gardenhub.db.connection import get_conn




def get_first_soil_moisture_today(bed_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT moisture_raw
            FROM sensor_readings
            WHERE bed_id = ?
              AND date = ?
            ORDER BY timestamp ASC
            LIMIT 1
        """, (bed_id, date.today().isoformat()))

        row = cur.fetchone()

    if row is None:
        raise ValueError("No soil reading for today")

    return int(row[0])

