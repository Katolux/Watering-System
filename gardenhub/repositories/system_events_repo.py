from datetime import datetime, timezone
import sqlite3

from gardenhub.db.connection import get_conn

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


def get_recent_system_event_records(limit=100):
    """Return complete event records for user-facing notification views.

    The existing tuple-returning helpers remain unchanged for the Home and
    Garden Control templates. Notifications also need the stored record id,
    date, and optional details so they can expose all information that already
    exists without changing the database schema.
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, timestamp, date, level, source, bed_id, message, details
            FROM system_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]
