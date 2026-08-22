"""Read-only view models shared by the GardenHub demo surfaces."""

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

from gardenhub.db.connection import get_conn
from gardenhub.demo_config import DEMO_GARDEN
from gardenhub.repositories.weather_repo import get_weather_records
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


WEATHER_CODES = {
    0: ("Clear", "sun"),
    1: ("Mainly clear", "sun"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "cloud"),
    48: ("Rime fog", "cloud"),
    51: ("Light drizzle", "rain"),
    53: ("Drizzle", "rain"),
    55: ("Heavy drizzle", "rain"),
    56: ("Freezing drizzle", "rain"),
    57: ("Heavy freezing drizzle", "rain"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "rain"),
    67: ("Heavy freezing rain", "rain"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Light rain showers", "rain"),
    81: ("Rain showers", "rain"),
    82: ("Heavy rain showers", "rain"),
    85: ("Snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Severe thunderstorm", "storm"),
}


def _weather_condition(code):
    try:
        return WEATHER_CODES.get(int(code), ("Conditions unavailable", "cloud"))
    except (TypeError, ValueError):
        return "Conditions unavailable", "cloud"


def _updated_label(value):
    if not value:
        return "Update time unavailable"
    try:
        updated = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        minutes = max(0, int((datetime.now(timezone.utc) - updated).total_seconds() / 60))
    except (TypeError, ValueError):
        return "Update time unavailable"
    if minutes < 1:
        return "Updated just now"
    if minutes < 60:
        return f"Updated {minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"Updated {days} day{'s' if days != 1 else ''} ago"


def _chart_points(records, field, minimum, maximum):
    if not records:
        return ""
    spread = max(1, maximum - minimum)
    width = 520
    height = 172
    points = []
    for index, record in enumerate(records):
        value = record.get(field)
        if value is None:
            continue
        x = 18 if len(records) == 1 else 18 + index * ((width - 36) / (len(records) - 1))
        y = 10 + (maximum - value) / spread * (height - 30)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _garden_impact(today):
    if not today:
        return "Weather guidance will appear after the next successful update."
    rain = today.get("precipitation") or 0
    wind = today.get("wind_max") or 0
    high = today.get("temp_max")
    if rain >= 10:
        return "Substantial rain is expected. Outdoor watering may not be needed."
    if rain >= 2:
        return "Rain is expected. Check soil conditions before watering."
    if high is not None and high >= 30:
        return "Hot conditions are expected. Check plants for heat stress."
    if wind >= 30:
        return "Strong wind is expected. Secure vulnerable pots and supports."
    return "Mild conditions are expected with no major weather pressure today."


def get_weather_snapshot(days=60, garden_context=None):
    garden_context = garden_context or get_garden_context()
    active_garden = get_active_garden(garden_context) or {}
    location = active_garden.get("location") or {}
    records = get_weather_records(days)
    today_date = datetime.now(timezone.utc).date()

    for record in records:
        record["date_value"] = date.fromisoformat(record["date"])
        record["condition"], record["condition_icon"] = _weather_condition(
            record.get("daily_weather_code")
        )
        record["day_label"] = record["date_value"].strftime("%a")
        record["date_label"] = (
            f"{record['date_value'].strftime('%b')} {record['date_value'].day}"
        )

    today = next((row for row in records if row["date_value"] == today_date), None)
    forecast = sorted(
        (row for row in records if row["date_value"] > today_date),
        key=lambda row: row["date_value"],
    )
    history = sorted(
        (row for row in records if row["date_value"] <= today_date),
        key=lambda row: row["date_value"],
    )
    chart_records = history[-7:]
    insight_records = history[-14:]

    current_code = today.get("current_weather_code") if today else None
    current_condition, current_icon = _weather_condition(current_code)
    current = {
        "temperature": today.get("current_temperature") if today else None,
        "humidity": today.get("current_humidity") if today else None,
        "pressure": today.get("current_pressure") if today else None,
        "wind_speed": today.get("current_wind_speed") if today else None,
        "wind_direction": today.get("current_wind_dir") if today else None,
        "condition": current_condition,
        "condition_icon": current_icon,
        "updated_label": _updated_label(
            (today.get("current_timestamp") or today.get("timestamp")) if today else None
        ),
    }

    temperatures = [
        value
        for row in chart_records
        for value in (row.get("temp_max"), row.get("temp_min"))
        if value is not None
    ]
    chart_min = min(temperatures) - 2 if temperatures else 0
    chart_max = max(temperatures) + 2 if temperatures else 1
    for row in chart_records:
        if row.get("temp_max") is not None and row.get("temp_min") is not None:
            row["temp_average"] = (row["temp_max"] + row["temp_min"]) / 2
        else:
            row["temp_average"] = None

    rain_max = max(
        [row.get("precipitation") or 0 for row in chart_records] or [1]
    )
    rain_width = 54 if chart_records else 0
    for index, row in enumerate(chart_records):
        row["rain_x"] = 22 + index * 72
        row["rain_height"] = (
            ((row.get("precipitation") or 0) / rain_max * 140) if rain_max else 0
        )
        row["rain_y"] = 154 - row["rain_height"]
        row["rain_width"] = rain_width

    total_rain = sum(row.get("precipitation") or 0 for row in insight_records)
    wet_days = sum(1 for row in insight_records if (row.get("precipitation") or 0) > 0)
    dry_days = len(insight_records) - wet_days
    highs = [row["temp_max"] for row in insight_records if row.get("temp_max") is not None]
    lows = [row["temp_min"] for row in insight_records if row.get("temp_min") is not None]
    winds = [row["wind_max"] for row in insight_records if row.get("wind_max") is not None]

    insights = [
        {
            "icon": "rain",
            "text": (
                f"{total_rain:.1f} mm of rain across {wet_days} wet "
                f"day{'s' if wet_days != 1 else ''}"
            ),
        },
        {
            "icon": "sun",
            "text": f"{dry_days} dry day{'s' if dry_days != 1 else ''} in the selected period",
        },
    ]
    if highs and lows:
        insights.append(
            {
                "icon": "thermometer",
                "text": f"Recorded range: {min(lows):.1f}°C to {max(highs):.1f}°C",
            }
        )
    if winds:
        insights.append(
            {"icon": "wind", "text": f"Strongest recorded wind: {max(winds):.1f} km/h"}
        )
    if len(insight_records) >= 14:
        previous = insight_records[:7]
        latest = insight_records[-7:]
        previous_average = sum(
            (row["temp_max"] + row["temp_min"]) / 2 for row in previous
        ) / len(previous)
        latest_average = sum(
            (row["temp_max"] + row["temp_min"]) / 2 for row in latest
        ) / len(latest)
        change = latest_average - previous_average
        insights.append(
            {
                "icon": "trend",
                "text": (
                    f"Average temperature is {abs(change):.1f}°C "
                    f"{'warmer' if change >= 0 else 'cooler'} than the previous week"
                ),
            }
        )

    return {
        "location": {
            **location,
            "label": location.get("address_label")
            or (
                f"{location['latitude']:.4f}°N, {location['longitude']:.4f}°E"
                if location.get("latitude") is not None
                and location.get("longitude") is not None
                else "Location unavailable"
            ),
        },
        "current": current,
        "today": today,
        "forecast": forecast,
        "history": list(reversed(history)),
        "chart": {
            "records": chart_records,
            "minimum": chart_min,
            "maximum": chart_max,
            "high_points": _chart_points(chart_records, "temp_max", chart_min, chart_max),
            "low_points": _chart_points(chart_records, "temp_min", chart_min, chart_max),
            "average_points": _chart_points(
                chart_records, "temp_average", chart_min, chart_max
            ),
            "rain_max": rain_max,
        },
        "summary": {
            "days": len(insight_records),
            "total_rain": total_rain,
            "wet_days": wet_days,
            "dry_days": dry_days,
            "highest": max(highs) if highs else None,
            "lowest": min(lows) if lows else None,
            "strongest_wind": max(winds) if winds else None,
        },
        "garden_impact": _garden_impact(today),
        "insights": insights,
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
