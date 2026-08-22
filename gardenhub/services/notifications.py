"""Presentation helpers for the existing GardenHub system-event stream."""

import json
from datetime import datetime, timezone

from gardenhub.repositories.system_events_repo import (
    get_recent_system_event_records,
)


CATEGORY_ORDER = (
    "Garden",
    "Weather",
    "Sensors",
    "Automation",
    "Watering",
    "Controller",
    "System",
)

CATEGORY_ICONS = {
    "Garden": "sprout",
    "Weather": "cloud",
    "Sensors": "wifi",
    "Automation": "automation",
    "Watering": "droplet",
    "Controller": "automation",
    "System": "activity",
}

LEVEL_PRESENTATION = {
    "INFO": ("Information", "info", "info"),
    "SUCCESS": ("Success", "success", "check"),
    "OK": ("Success", "success", "check"),
    "WARNING": ("Warning", "warning", "alert"),
    "ERROR": ("Error", "critical", "alert"),
    "CRITICAL": ("Critical", "critical", "alert"),
}

ATTENTION_LEVELS = {"WARNING", "ERROR", "CRITICAL"}


def _category_for(source, message=None):
    source_key = (source or "").strip().lower()
    message_key = (message or "").strip().lower()
    if "watering_engine" in source_key or "automation" in source_key:
        return "Automation"
    if "scheduler" in source_key:
        if "weather" in message_key or "forecast" in message_key:
            return "Weather"
        if any(word in message_key for word in ("watering", "engine", "slot")):
            return "Automation"
    if "water" in source_key or "irrigat" in source_key:
        return "Watering"
    if "sensor" in source_key or "moisture" in source_key:
        return "Sensors"
    if "weather" in source_key or "forecast" in source_key:
        return "Weather"
    if any(word in source_key for word in ("controller", "hardware", "arduino", "esp32", "node")):
        return "Controller"
    if any(word in source_key for word in ("garden", "bed", "plant", "catalog")):
        return "Garden"
    return "System"


def _destination_for(category, source):
    source_key = (source or "").strip().lower()
    if category == "Watering":
        return "/watering", "Open Watering"
    if category == "Sensors":
        return "/automation/sensors", "Open Sensors"
    if category == "Weather":
        return "/weather", "Open Weather"
    if category == "Automation":
        return "/automation", "Open Garden Control"
    if category == "Controller":
        return "/automation", "Open Garden Control"
    if category == "Garden":
        if "catalog" in source_key or "plant" in source_key:
            return "/automation/plants", "Open Encyclopedia"
        if "bed" in source_key:
            return "/automation/beds", "Open Beds"
        return "/automation", "Open Garden Control"
    return "/automation#system-events", "Open system events"


def _timestamp_presentation(value):
    if not value:
        return "Time unavailable", None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
        return (
            f"{parsed.day} {parsed.strftime('%b %Y')}, {parsed.strftime('%H:%M')} UTC",
            parsed.isoformat(),
        )
    except (TypeError, ValueError):
        return str(value), str(value)


def _detail_items(value):
    if value is None or value == "":
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return [{"label": "Recorded details", "value": str(value)}]
    if isinstance(parsed, dict):
        return [
            {
                "label": str(key).replace("_", " ").strip().title(),
                "value": value if isinstance(value, str) else json.dumps(value),
            }
            for key, value in parsed.items()
        ]
    return [{"label": "Recorded details", "value": json.dumps(parsed)}]


def _present_event(record):
    level = (record.get("level") or "INFO").strip().upper()
    level_label, tone, icon = LEVEL_PRESENTATION.get(
        level, (level.title() or "Information", "info", "info")
    )
    category = _category_for(record.get("source"), record.get("message"))
    destination_href, destination_label = _destination_for(
        category, record.get("source")
    )
    timestamp_label, timestamp_value = _timestamp_presentation(
        record.get("timestamp")
    )
    return {
        **record,
        "level": level,
        "level_label": level_label,
        "tone": tone,
        "icon": icon,
        "category": category,
        "category_key": category.lower(),
        "category_icon": CATEGORY_ICONS[category],
        "source_label": (record.get("source") or "System")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title(),
        "bed_label": (
            str(record["bed_id"]).replace("_", " ").replace("-", " ").title()
            if record.get("bed_id")
            else None
        ),
        "timestamp_label": timestamp_label,
        "timestamp_value": timestamp_value,
        "is_attention": level in ATTENTION_LEVELS,
        "detail_items": _detail_items(record.get("details")),
        "destination_href": destination_href,
        "destination_label": destination_label,
    }


def get_notification_feed(limit=100, preview_limit=4):
    """Build one frontend view of the existing event stream.

    Warning and error records are labelled as needing review, never as active or
    unread: neither durable state exists in the current backend.
    """
    records = get_recent_system_event_records(limit=limit)
    events = [_present_event(record) for record in records]
    attention_events = [event for event in events if event["is_attention"]]
    informational_events = [event for event in events if not event["is_attention"]]
    recent_window = events[:20]
    preview = [event for event in recent_window if event["is_attention"]]
    preview.extend(event for event in recent_window if not event["is_attention"])
    preview = preview[:preview_limit]
    available_categories = [
        category
        for category in CATEGORY_ORDER
        if any(event["category"] == category for event in events)
    ]
    return {
        "events": events,
        "preview": preview,
        "attention_events": attention_events,
        "attention_count": len(attention_events),
        "information_count": len(informational_events),
        "available_categories": available_categories,
        "category_count": len(available_categories),
        "state_is_persistent": False,
        "load_error": False,
    }


def unavailable_notification_feed():
    return {
        "events": [],
        "preview": [],
        "attention_events": [],
        "attention_count": 0,
        "information_count": 0,
        "available_categories": [],
        "category_count": 0,
        "state_is_persistent": False,
        "load_error": True,
    }
