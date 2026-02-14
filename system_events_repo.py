from datetime import datetime, timezone
from db import get_conn

def log_system_event(level, source, message, bed_id=None, details=None):
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    date_str = now.date().isoformat()

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO system_events (
                timestamp, date, level, source, bed_id, message, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            date_str,
            level,
            source,
            bed_id,
            message,
            details
        ))
        conn.commit()


def get_system_events_by_date(date_str, limit=50):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, level, source, bed_id, message
            FROM system_events
            WHERE date = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (date_str, limit))
        return cur.fetchall()


def get_recent_system_events(limit=50):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, level, source, bed_id, message
            FROM system_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()
