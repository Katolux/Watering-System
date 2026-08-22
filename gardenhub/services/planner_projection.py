"""Read-only presentation of persisted Planner geometry for Garden Control."""

import re

from gardenhub.services.planner_layout import load_planner_layout


def _css_token(value):
    token = re.sub(r"[^a-z0-9-]+", "-", str(value or "").lower()).strip("-")
    return token or "default"


def _bed_operational_state(bed, garden):
    bed_id = bed["bed_id"]
    sensors = [sensor for sensor in garden["sensors"] if sensor["bed_id"] == bed_id]
    events = [
        event
        for event in garden["events"]
        if event.get("bed_id") == bed_id and event.get("level") == "ERROR"
    ]
    events.extend(
        {**warning, "level": "WARNING"}
        for warning in garden["warnings"]
        if warning.get("bed_id") == bed_id
    )
    watering = next(
        (event for event in garden["watering_events"] if event.get("bed_id") == bed_id),
        None,
    )
    decision = next(
        (item for item in garden["decisions"] if item.get("bed_id") == bed_id),
        None,
    )

    if not bed["active"]:
        status = "resting"
        status_label = "Resting"
    elif any(event["level"] == "ERROR" for event in events):
        status = "warning"
        status_label = "Error"
    elif events:
        status = "warning"
        status_label = "Warning"
    elif sensors and any(not sensor["active"] for sensor in sensors):
        status = "warning"
        status_label = "Sensor offline"
    elif not bed["active_sensor_count"]:
        status = "warning"
        status_label = "Sensor needed"
    elif bed["moisture"] is None:
        status = "warning"
        status_label = "Awaiting data"
    elif bed["moisture"] < 45 or bed["moisture"] > 75:
        status = "warning"
        status_label = f"{int(bed['moisture'])}% moisture"
    else:
        status = "healthy"
        status_label = f"{int(bed['moisture'])}% moisture"

    return {
        "status": status,
        "status_label": status_label,
        "sensors": sensors,
        "watering": watering,
        "decision": decision,
        "events": events,
    }


def get_planner_projection(garden_id, garden):
    """Join saved Planner objects to the operational rows Garden Control owns.

    Geometry is kept in the Planner contract. Percentages are derived only for
    responsive presentation; the source metre/foot values remain on each object.
    """

    saved = load_planner_layout(garden_id)
    if saved is None:
        return None

    width = saved["garden"]["width"]
    height = saved["garden"]["height"]
    beds_by_id = {bed["bed_id"]: bed for bed in garden["beds"]}
    objects = []

    ordered = sorted(
        enumerate(saved["objects"]),
        key=lambda indexed: (indexed[1].get("z", indexed[0]), indexed[0]),
    )
    for display_order, (_, source) in enumerate(ordered, start=1):
        item = dict(source)
        item["left_pct"] = round(item["x"] / width * 100, 6)
        item["top_pct"] = round(item["y"] / height * 100, 6)
        item["width_pct"] = round(item["width"] / width * 100, 6)
        item["height_pct"] = round(item["height"] / height * 100, 6)
        item["display_order"] = display_order
        item["kind_class"] = _css_token(item["kind"])
        item["variant_class"] = _css_token(item.get("variant"))
        item["operational"] = None

        bed_id = item.get("bedId")
        if item["kind"] == "bed" and bed_id in beds_by_id:
            bed = beds_by_id[bed_id]
            item["domain_bed"] = bed
            item["operational"] = _bed_operational_state(bed, garden)
        objects.append(item)

    units = saved["garden"].get("units") or "m"
    bed_count = sum(item["kind"] == "bed" for item in objects)
    linked_bed_count = sum(item.get("operational") is not None for item in objects)
    return {
        "version": saved["schema_version"],
        "updated_at": saved["updated_at"],
        "garden": saved["garden"],
        "objects": objects,
        "aspect_ratio": round(width / height, 6),
        "dimensions_label": f"{width:g} × {height:g} {units}",
        "object_count": len(objects),
        "bed_count": bed_count,
        "linked_bed_count": linked_bed_count,
    }
