from datetime import datetime, timezone

from gardenhub.db.connection import get_conn


def get_garden_location():
    with get_conn() as conn:
        conn.row_factory = __import__("sqlite3").Row

        row = conn.execute(
            """
            SELECT
                id,
                location_label,
                latitude,
                longitude,
                timezone,
                updated_at
            FROM garden_location
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def save_garden_location(
    location_label,
    latitude,
    longitude,
    timezone_name,
):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO garden_location (
                id,
                location_label,
                latitude,
                longitude,
                timezone,
                updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?)

            ON CONFLICT(id) DO UPDATE SET
                location_label = excluded.location_label,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                timezone = excluded.timezone,
                updated_at = excluded.updated_at
            """,
            (
                location_label,
                latitude,
                longitude,
                timezone_name,
                datetime.now(timezone.utc).isoformat(),
            ),
        )