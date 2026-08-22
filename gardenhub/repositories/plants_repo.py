from datetime import datetime, timezone
from gardenhub.db.connection import get_conn
import json




# -----------------------------
# PLANTS
# -----------------------------


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


def get_encyclopedia_catalog():
    """Return the plant fields needed by the user-facing catalogue."""
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
                photo_key,
                spacing_in_row_cm,
                water_need_overall,
                calendar_json,
                plant_json
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


def get_encyclopedia_varieties(plant_id):
    """Return variety content used by the Encyclopedia, including resolved data."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                variety_id,
                name,
                notes,
                overrides_json,
                resolved_json
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


def get_encyclopedia_companions(plant_id):
    """Return companion relationships with user-facing plant names."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                other.plant_id,
                other.name,
                other.scientific_name,
                relation.relation,
                relation.reason,
                relation.confidence,
                relation.mechanism
            FROM plant_companions AS relation
            JOIN plants AS other
              ON other.plant_id = relation.other_plant_id
            WHERE relation.plant_id = ?
            ORDER BY
                CASE relation.relation WHEN 'good' THEN 0 ELSE 1 END,
                other.name COLLATE NOCASE
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
            None
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

        cur.execute("DELETE FROM plant_companions WHERE plant_id = ? OR other_plant_id = ?",(plant_id, plant_id))
        cur.execute("DELETE FROM plant_varieties WHERE plant_id = ?", (plant_id,))

        cur.execute("""
            UPDATE bed_plantings
            SET removed_at = ?
            WHERE plant_id = ? AND removed_at IS NULL
        """, (datetime.now(timezone.utc).isoformat(), plant_id))

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
