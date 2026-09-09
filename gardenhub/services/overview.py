"""Read-only view models shared by the GardenHub demo surfaces."""

import json
import math
from pathlib import Path

from gardenhub.db.connection import get_conn
from gardenhub.demo_config import DEMO_GARDEN
from gardenhub.services.garden_context import (
    get_active_garden,
    get_garden_context,
)


def _rows(query, params=()):
    with get_conn() as conn:
        conn.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_garden_snapshot():
    beds = _rows("""
        SELECT b.bed_id, b.zone_id, b.active, z.name AS zone_name,
               COUNT(DISTINCT bp.id) AS planting_count,
               (SELECT COALESCE(SUM(bp2.quantity), 0) FROM bed_plantings bp2
                WHERE bp2.bed_id = b.bed_id AND bp2.removed_at IS NULL) AS plant_count,
               GROUP_CONCAT(DISTINCT p.name) AS plant_names,
               COUNT(DISTINCT s.sensor_id) AS sensor_count,
               COUNT(DISTINCT CASE WHEN s.active = 1 THEN s.sensor_id END) AS active_sensor_count,
               (SELECT ROUND(AVG(sr.moisture_pct)) FROM sensor_readings sr
                WHERE sr.bed_id = b.bed_id AND sr.date = (SELECT MAX(date) FROM sensor_readings)) AS moisture
        FROM beds b
        LEFT JOIN zones z ON z.zone_id = b.zone_id
        LEFT JOIN bed_plantings bp ON bp.bed_id = b.bed_id AND bp.removed_at IS NULL
        LEFT JOIN plants p ON p.plant_id = bp.plant_id
        LEFT JOIN sensors s ON s.bed_id = b.bed_id
        GROUP BY b.bed_id, b.zone_id, b.active, z.name
        ORDER BY b.bed_id
    """)
    for bed in beds:
        bed["plants"] = bed.pop("plant_names").split(",") if bed.get("plant_names") else []

    counts = {}
    for table in ("plants", "plant_varieties", "zones", "bed_plantings", "sensors", "sensor_readings"):
        counts[table] = _rows(f"SELECT COUNT(*) AS count FROM {table}")[0]["count"]
    counts["active_sensors"] = _rows("SELECT COUNT(*) AS count FROM sensors WHERE active = 1")[0]["count"]
    counts["warnings"] = _rows("SELECT COUNT(*) AS count FROM system_events WHERE level = 'WARNING'")[0]["count"]
    counts["total_plants"] = _rows(
        "SELECT COALESCE(SUM(quantity), 0) AS count FROM bed_plantings WHERE removed_at IS NULL"
    )[0]["count"]
    counts["greenhouses"] = _rows(
        "SELECT COUNT(*) AS count FROM beds WHERE LOWER(bed_id) LIKE '%greenhouse%'"
    )[0]["count"]

    zones = _rows("""
        SELECT z.zone_id, z.name, z.active,
               COUNT(DISTINCT b.bed_id) AS bed_count,
               GROUP_CONCAT(DISTINCT b.bed_id) AS bed_names,
               COUNT(DISTINCT s.sensor_id) AS sensor_count,
               COUNT(DISTINCT CASE WHEN s.active = 1 THEN s.sensor_id END) AS active_sensor_count
        FROM zones z
        LEFT JOIN beds b ON b.zone_id = z.zone_id
        LEFT JOIN sensors s ON s.bed_id = b.bed_id
        GROUP BY z.zone_id, z.name, z.active
        ORDER BY z.name
    """)
    for zone in zones:
        zone["beds"] = zone.pop("bed_names").split(",") if zone.get("bed_names") else []
        if not zone["active"]:
            zone["status"] = "inactive"
        elif zone["active_sensor_count"]:
            zone["status"] = "monitoring"
        else:
            zone["status"] = "review"

    environment = _rows("""
        SELECT ROUND(AVG(moisture_pct), 1) AS soil_moisture
        FROM sensor_readings
        WHERE date = (SELECT MAX(date) FROM sensor_readings)
    """)[0]

    return {
        "counts": counts,
        "beds": beds,
        "zones": zones,
        "environment": environment,
        "sensors": _rows("""
            SELECT s.sensor_id, s.bed_id, s.sensor_type, s.depth_cm, s.active,
                   (SELECT sr.moisture_pct FROM sensor_readings sr WHERE sr.sensor_id = s.sensor_id
                    ORDER BY sr.timestamp DESC LIMIT 1) AS latest_moisture
            FROM sensors s ORDER BY s.bed_id, s.sensor_id
        """),
        "decisions": _rows("SELECT * FROM watering_decisions ORDER BY timestamp DESC LIMIT 10"),
        "watering_events": _rows("SELECT * FROM watering_events ORDER BY timestamp DESC LIMIT 12"),
        "events": _rows("SELECT timestamp, date, level, source, bed_id, message FROM system_events ORDER BY timestamp DESC LIMIT 12"),
        "warnings": _rows("SELECT timestamp, source, bed_id, message FROM system_events WHERE level = 'WARNING' ORDER BY timestamp DESC"),
    }



def get_planner_catalog():
    plants = _rows("""
        SELECT plant_id, name, scientific_name, category, family, icon_key,
               spacing_in_row_cm, spacing_between_rows_cm, water_need_overall,
               calendar_json, plant_json
        FROM plants ORDER BY name COLLATE NOCASE
    """)
    companions = _rows("""
        SELECT relation.plant_id, relation.other_plant_id, other.name,
               relation.relation, relation.reason, relation.confidence,
               relation.mechanism
        FROM plant_companions AS relation
        JOIN plants AS other ON other.plant_id = relation.other_plant_id
        ORDER BY relation.plant_id, relation.relation, other.name COLLATE NOCASE
    """)
    by_plant = {}
    for companion in companions:
        by_plant.setdefault(companion.pop("plant_id"), []).append(companion)

    asset_root = Path(__file__).resolve().parents[2] / "static" / "images" / "botanical" / "planner"
    for plant in plants:
        try:
            calendar = json.loads(plant.pop("calendar_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            calendar = {}
        try:
            document = json.loads(plant.pop("plant_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            document = {}
        base_calendar = calendar.get("base") or document.get("calendar", {}).get("base", {})
        plant["calendar"] = {
            key: {
                "months": [month for month in (base_calendar.get(key, {}).get("months") or []) if isinstance(month, int) and 1 <= month <= 12],
                "notes": base_calendar.get(key, {}).get("notes"),
            }
            for key in ("sow_indoors", "sow_outdoors", "transplant_out", "harvest")
            if base_calendar.get(key)
        }
        icon_key = Path(plant.get("icon_key") or plant["plant_id"]).stem
        plant["icon_key"] = icon_key
        plant["asset_path"] = f"images/botanical/planner/{icon_key}.png"
        plant["has_asset"] = (asset_root / f"{icon_key}.png").is_file()
        plant["companions"] = by_plant.get(plant["plant_id"], [])
        plant["encyclopedia_path"] = f"/automation/plants/{plant['plant_id']}"
    return plants


def get_planner_state(catalog=None, garden_context=None):
    """Load saved Planner geometry or build the optional domain-linked template."""
    catalog = catalog or get_planner_catalog()
    garden_context = garden_context or get_garden_context()
    active_garden = get_active_garden(garden_context) or {}
    from gardenhub.services.planner_layout import load_planner_layout

    saved_layout = load_planner_layout(garden_context["active_garden_id"])
    if saved_layout is not None:
        return {
            "version": saved_layout["schema_version"],
            "planExists": True,
            "garden": saved_layout["garden"],
            "objects": saved_layout["objects"],
            "persistence": "backend",
            "updatedAt": saved_layout["updated_at"],
            "greenhouse": {
                "rulesAvailable": False,
                "message": "Season extension not yet implemented",
            },
        }
    plants = {plant["plant_id"]: plant for plant in catalog}
    beds = _rows("""
        SELECT b.bed_id, b.active, b.zone_id, z.name AS zone_name
        FROM beds b LEFT JOIN zones z ON z.zone_id = b.zone_id
        ORDER BY b.bed_id
    """)
    assignments = _rows("""
        SELECT bp.id, bp.bed_id, bp.plant_id, bp.quantity
        FROM bed_plantings bp
        WHERE bp.removed_at IS NULL
        ORDER BY bp.bed_id, bp.id
    """)
    assignments_by_bed = {}
    for assignment in assignments:
        assignments_by_bed.setdefault(assignment["bed_id"], []).append(assignment)

    width_m = DEMO_GARDEN["width_m"]
    height_m = DEMO_GARDEN["height_m"]
    objects = []
    bed_geometry = {}
    for index, bed in enumerate(beds):
        layout = DEMO_GARDEN["beds"].get(bed["bed_id"])
        if layout:
            geometry = {
                "x": round(layout["x"] / 100 * width_m, 2),
                "y": round(layout["y"] / 100 * height_m, 2),
                "width": round(layout["w"] / 100 * width_m, 2),
                "height": round(layout["h"] / 100 * height_m, 2),
            }
        else:
            geometry = {
                "x": 1 + (index % 3) * 7.5,
                "y": 1 + (index // 3) * 4.8,
                "width": 6,
                "height": 3.6,
            }
        bed_geometry[bed["bed_id"]] = geometry
        objects.append({
            "id": f"bed-{bed['bed_id']}",
            "kind": "bed",
            "variant": "greenhouse" if "greenhouse" in bed["bed_id"].lower() else "raised-bed",
            "layer": "beds",
            "name": bed["bed_id"].replace("-", " ").title(),
            "bedId": bed["bed_id"],
            "zoneName": bed.get("zone_name") or "Unassigned zone",
            "active": bool(bed["active"]),
            "rotation": 0,
            **geometry,
        })

    for bed_id, bed_assignments in assignments_by_bed.items():
        geometry = bed_geometry.get(bed_id)
        if not geometry:
            continue
        cursor_y = geometry["y"] + 0.45
        for assignment in bed_assignments:
            plant = plants.get(assignment["plant_id"])
            if not plant:
                continue
            spacing_x = max((plant.get("spacing_in_row_cm") or 30) / 100, 0.1)
            spacing_y = max((plant.get("spacing_between_rows_cm") or plant.get("spacing_in_row_cm") or 30) / 100, 0.1)
            available_width = max(geometry["width"] - 0.9, spacing_x)
            columns = max(1, min(int(assignment["quantity"] or 1), math.floor(available_width / spacing_x)))
            rows = max(1, math.ceil((assignment["quantity"] or 1) / columns))
            footprint_width = min(available_width, columns * spacing_x)
            footprint_height = rows * spacing_y
            if cursor_y + footprint_height > geometry["y"] + geometry["height"] - 0.3:
                cursor_y = geometry["y"] + 0.45
            objects.append({
                "id": f"planting-{assignment['id']}",
                "kind": "plant",
                "layer": "plants",
                "name": plant["name"],
                "plantId": plant["plant_id"],
                "bedId": bed_id,
                "x": round(geometry["x"] + 0.45, 2),
                "y": round(cursor_y, 2),
                "width": round(footprint_width, 2),
                "height": round(footprint_height, 2),
                "rotation": 0,
                "quantity": int(assignment["quantity"] or 1),
                "sourcePlantingId": assignment["id"],
            })
            cursor_y += footprint_height + 0.3

    return {
        "version": 2,
        "planExists": False,
        "garden": {
            "name": active_garden.get("name") or "Garden",
            "width": width_m,
            "height": height_m,
            "units": "m",
            "north": 0,
        },
        "objects": objects,
        "persistence": "not-yet-saved",
        "greenhouse": {
            "rulesAvailable": False,
            "message": "Season extension not yet implemented",
        },
    }
