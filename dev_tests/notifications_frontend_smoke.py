"""Focused smoke checks for the system-event notifications frontend."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ["GARDENHUB_DB_PATH"] = str(
    (BASE_DIR / "dev_data" / "gardenhub_demo.db").resolve()
)

from app import app  # noqa: E402
from gardenhub.routes import notification_routes  # noqa: E402
from gardenhub.services.notifications import unavailable_notification_feed  # noqa: E402


def _empty_feed():
    return {
        "events": [],
        "preview": [],
        "attention_events": [],
        "attention_count": 0,
        "information_count": 0,
        "available_categories": [],
        "category_count": 0,
        "state_is_persistent": False,
        "load_error": False,
    }


def run():
    client = app.test_client()
    routes = (
        "/",
        "/automation",
        "/weather",
        "/planner",
        "/automation/beds",
        "/automation/sensors",
        "/watering",
        "/automation/plants",
        "/notifications",
    )
    statuses = {route: client.get(route).status_code for route in routes}
    assert all(status == 200 for status in statuses.values()), statuses

    notification_page = client.get("/notifications").get_data(as_text=True)
    workspace_page = client.get("/").get_data(as_text=True)
    assert "Inactive demo sensor requires review" in notification_page
    assert "Data Status" in notification_page
    assert 'data-notification-filter="sensors"' in notification_page
    assert 'data-notification-filter="automation"' in notification_page
    assert "Selected system event" in notification_page
    assert "The historical record of what GardenHub has done" in notification_page
    assert "does not track unread" in notification_page
    assert "View all notifications" in workspace_page
    assert "Inactive demo sensor requires review" in workspace_page

    original_feed = notification_routes.get_notification_feed
    try:
        notification_routes.get_notification_feed = _empty_feed
        empty_page = client.get("/notifications").get_data(as_text=True)
        assert "All quiet in the garden" in empty_page

        notification_routes.get_notification_feed = lambda: unavailable_notification_feed()
        error_page = client.get("/notifications").get_data(as_text=True)
        assert "Notifications are temporarily unavailable" in error_page
    finally:
        notification_routes.get_notification_feed = original_feed

    notification_rule = next(
        rule for rule in app.url_map.iter_rules() if rule.endpoint == "notifications.notifications"
    )
    assert notification_rule.rule == "/notifications"
    assert "GET" in notification_rule.methods

    print({
        "routes": statuses,
        "notification_route": notification_rule.rule,
        "demo_events": True,
        "bell_preview": True,
        "filters_and_details": True,
        "empty_state": True,
        "load_error_state": True,
    })


if __name__ == "__main__":
    run()
