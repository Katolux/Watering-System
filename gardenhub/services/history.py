"""Read-only presentation model for the cross-system Garden History hub."""

from datetime import date, datetime, time, timezone

from gardenhub.repositories.sensors_repo import get_recent_sensor_readings
from gardenhub.repositories.system_events_repo import get_recent_system_event_records
from gardenhub.repositories.watering_repo import get_recent_watering_events
from gardenhub.repositories.weather_repo import get_weather_records
from gardenhub.services.notifications import _present_event
from gardenhub.services.overview import WEATHER_CODES


CATEGORY_DEFINITIONS = (
    {
        "key": "all",
        "label": "All",
        "empty_title": "No garden activity recorded yet.",
        "empty_text": "Weather, sensor, watering and system records will appear here when they are stored.",
    },
    {
        "key": "weather",
        "label": "Weather",
        "empty_title": "No weather activity recorded yet.",
        "empty_text": "Stored daily weather records will appear here when they are available.",
    },
    {
        "key": "sensors",
        "label": "Sensors",
        "empty_title": "No sensor activity recorded yet.",
        "empty_text": "Stored sensor readings will appear here when they are available.",
    },
    {
        "key": "watering",
        "label": "Watering",
        "empty_title": "No watering activity recorded yet.",
        "empty_text": "Stored watering events will appear here when they are available.",
    },
    {
        "key": "system",
        "label": "System",
        "empty_title": "No system activity recorded yet.",
        "empty_text": "Stored warnings and system events will appear here when they are available.",
    },
)


def _as_utc(value, fallback_date=None):
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError):
            pass
    if fallback_date:
        try:
            parsed_date = date.fromisoformat(str(fallback_date))
            return datetime.combine(parsed_date, time.max, tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def _timestamp_fields(timestamp, *, date_only=False):
    if timestamp == datetime.min.replace(tzinfo=timezone.utc):
        return "Time unavailable", None
    if date_only:
        label = f"{timestamp.day} {timestamp.strftime('%b %Y')}"
    else:
        label = f"{timestamp.day} {timestamp.strftime('%b %Y')}, {timestamp.strftime('%H:%M')} UTC"
    return label, timestamp.isoformat()


def _humanize(value, fallback="Unavailable"):
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).replace("_", " ").replace("-", " ").strip().title()


def _weather_condition(code):
    try:
        return WEATHER_CODES.get(int(code), ("Daily weather", "cloud"))
    except (TypeError, ValueError):
        return "Daily weather", "cloud"


def _weather_events(limit):
    today = date.today()
    events = []
    for record in get_weather_records(days=limit):
        try:
            record_date = date.fromisoformat(record["date"])
        except (KeyError, TypeError, ValueError):
            continue
        if record_date > today:
            continue

        timestamp = _as_utc(None, record_date)
        timestamp_label, timestamp_value = _timestamp_fields(timestamp, date_only=True)
        condition, icon = _weather_condition(record.get("daily_weather_code"))
        facts = []
        if record.get("precipitation") is not None:
            facts.append(f"{record['precipitation']:.1f} mm rain")
        if record.get("temp_max") is not None:
            facts.append(f"High {record['temp_max']:.1f}\N{DEGREE SIGN}C")
        if record.get("temp_min") is not None:
            facts.append(f"Low {record['temp_min']:.1f}\N{DEGREE SIGN}C")

        events.append({
            "id": f"weather-{record_date.isoformat()}",
            "category": "weather",
            "category_label": "Weather",
            "icon": icon,
            "title": f"{condition} recorded",
            "secondary": " \N{MIDDLE DOT} ".join(facts) or "Daily weather values unavailable",
            "timestamp": timestamp,
            "timestamp_label": timestamp_label,
            "timestamp_value": timestamp_value,
            "destination_href": "/weather?tab=history",
            "destination_label": "View weather history",
        })
    return events


def _sensor_events(limit):
    events = []
    for timestamp_value, _, bed_id, sensor_id, slot, _, moisture_pct in get_recent_sensor_readings(limit=limit):
        timestamp = _as_utc(timestamp_value)
        timestamp_label, normalized_timestamp = _timestamp_fields(timestamp)
        facts = []
        if bed_id:
            facts.append(_humanize(bed_id))
        if moisture_pct is not None:
            facts.append(f"{moisture_pct}%")
        if sensor_id:
            facts.append(str(sensor_id))
        if slot is not None:
            facts.append(f"Slot {slot}")
        events.append({
            "id": f"sensor-{sensor_id}-{timestamp.isoformat()}",
            "category": "sensors",
            "category_label": "Sensors",
            "icon": "wifi",
            "title": "Soil moisture reading",
            "secondary": " \N{MIDDLE DOT} ".join(facts) or "Reading details unavailable",
            "timestamp": timestamp,
            "timestamp_label": timestamp_label,
            "timestamp_value": normalized_timestamp,
            "destination_href": "/automation/sensors",
            "destination_label": "Open Sensors",
        })
    return events


def _watering_events(limit):
    events = []
    for timestamp_value, bed_id, minutes, mode, _, note in get_recent_watering_events(limit=limit):
        timestamp = _as_utc(timestamp_value)
        timestamp_label, normalized_timestamp = _timestamp_fields(timestamp)
        facts = []
        if bed_id:
            facts.append(_humanize(bed_id))
        if minutes is not None:
            facts.append(f"{minutes} min")
        if mode:
            facts.append(_humanize(mode))
        if note:
            facts.append(str(note))
        events.append({
            "id": f"watering-{timestamp.isoformat()}-{bed_id or 'unknown'}",
            "category": "watering",
            "category_label": "Watering",
            "icon": "droplet",
            "title": "Watering recorded",
            "secondary": " \N{MIDDLE DOT} ".join(facts) or "Watering details unavailable",
            "timestamp": timestamp,
            "timestamp_label": timestamp_label,
            "timestamp_value": normalized_timestamp,
            "destination_href": "/watering",
            "destination_label": "Open Watering",
        })
    return events


def _system_events(limit):
    events = []
    for record in get_recent_system_event_records(limit=limit):
        presented = _present_event(record)
        timestamp = _as_utc(record.get("timestamp"), record.get("date"))
        timestamp_label, normalized_timestamp = _timestamp_fields(timestamp)
        facts = [presented["level_label"], f"From {presented['source_label']}"]
        if presented.get("bed_label"):
            facts.append(presented["bed_label"])
        events.append({
            "id": f"system-{record['id']}",
            "category": "system",
            "category_label": "System",
            "icon": presented["icon"],
            "title": record.get("message") or "System event recorded",
            "secondary": " \N{MIDDLE DOT} ".join(facts),
            "timestamp": timestamp,
            "timestamp_label": timestamp_label,
            "timestamp_value": normalized_timestamp,
            "destination_href": f"/notifications#event-{record['id']}",
            "destination_label": "View system event",
            "tone": presented["tone"],
        })
    return events


def get_garden_history(per_source_limit=100, timeline_limit=250):
    """Combine existing records for display without creating unified storage."""
    loaders = {
        "weather": _weather_events,
        "sensors": _sensor_events,
        "watering": _watering_events,
        "system": _system_events,
    }
    events = []
    source_status = {}

    for category, loader in loaders.items():
        try:
            category_events = loader(per_source_limit)
        except Exception:
            category_events = []
            source_status[category] = "unavailable"
        else:
            source_status[category] = "available"
        events.extend(category_events)

    events.sort(key=lambda event: event["timestamp"], reverse=True)
    events = events[:timeline_limit]
    counts = {
        category["key"]: sum(
            1 for event in events if event["category"] == category["key"]
        )
        for category in CATEGORY_DEFINITIONS
        if category["key"] != "all"
    }
    counts["all"] = len(events)

    categories = []
    for definition in CATEGORY_DEFINITIONS:
        category = {**definition, "count": counts[definition["key"]]}
        status = source_status.get(definition["key"])
        category["available"] = status != "unavailable"
        if status == "unavailable":
            category["empty_title"] = f"{definition['label']} history is unavailable."
            category["empty_text"] = "GardenHub could not load this existing data source right now."
        categories.append(category)

    return {
        "events": events,
        "categories": categories,
        "source_status": source_status,
        "has_unavailable_sources": any(
            status == "unavailable" for status in source_status.values()
        ),
    }
