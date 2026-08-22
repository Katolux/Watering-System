import json
from datetime import datetime, timezone

from gardenhub.db.connection import get_conn


def get_planner_layout(garden_id):
    conn = get_conn()
    try:
        conn.row_factory = __import__("sqlite3").Row
        row = conn.execute(
            """
            SELECT garden_id, schema_version, garden_json, objects_json, updated_at
            FROM planner_layouts
            WHERE garden_id = ?
            """,
            (garden_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "garden_id": row["garden_id"],
        "schema_version": row["schema_version"],
        "garden": json.loads(row["garden_json"]),
        "objects": json.loads(row["objects_json"]),
        "updated_at": row["updated_at"],
    }


def save_planner_layout(garden_id, schema_version, garden, objects):
    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    garden_json = json.dumps(garden, separators=(",", ":"), sort_keys=True)
    objects_json = json.dumps(objects, separators=(",", ":"), sort_keys=True)
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO planner_layouts
                (garden_id, schema_version, garden_json, objects_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(garden_id) DO UPDATE SET
                schema_version = excluded.schema_version,
                garden_json = excluded.garden_json,
                objects_json = excluded.objects_json,
                updated_at = excluded.updated_at
            """,
            (garden_id, schema_version, garden_json, objects_json, updated_at),
        )
        conn.commit()
    finally:
        conn.close()
    return updated_at
