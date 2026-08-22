"""Focused smoke checks for the cross-system Garden History hub."""

import os
import sys
from pathlib import Path
from unittest.mock import patch


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ["GARDENHUB_DB_PATH"] = str(
    (BASE_DIR / "dev_data" / "gardenhub_demo.db").resolve()
)

from app import app  # noqa: E402
from gardenhub.services.history import get_garden_history  # noqa: E402


def run():
    client = app.test_client()
    response = client.get("/history", follow_redirects=False)
    page = response.get_data(as_text=True)
    weather_page = client.get("/weather?tab=history").get_data(as_text=True)
    history = get_garden_history()

    assert response.status_code == 200
    assert response.location is None
    assert "Garden History" in page
    assert "See recent weather, sensor, watering and system activity across your garden." in page
    assert 'href="/history" aria-current="page"' in page
    assert 'href="/weather" aria-current="page"' not in page
    assert "Weather History" in weather_page
    assert 'id="weather-panel-2"' in weather_page
    assert 'id="weather-panel-2" role="tabpanel" aria-labelledby="weather-tab-2" hidden' not in weather_page

    expected_categories = {"weather", "sensors", "watering", "system"}
    actual_categories = {event["category"] for event in history["events"]}
    assert expected_categories.issubset(actual_categories), actual_categories
    for category in ("all", *sorted(expected_categories)):
        assert f'data-history-filter="{category}"' in page
    for category in expected_categories:
        assert f'data-category="{category}"' in page

    assert "Daily weather recorded" in page
    assert "Soil moisture reading" in page
    assert "Watering recorded" in page
    assert "Inactive demo sensor requires review" in page

    with (
        patch("gardenhub.services.history.get_weather_records", return_value=[]),
        patch("gardenhub.services.history.get_recent_sensor_readings", return_value=[]),
        patch("gardenhub.services.history.get_recent_watering_events", return_value=[]),
        patch("gardenhub.services.history.get_recent_system_event_records", return_value=[]),
    ):
        empty_history = get_garden_history()
    with patch("app.get_garden_history", return_value=empty_history):
        empty_page = client.get("/history").get_data(as_text=True)
    assert "No garden activity recorded yet." in empty_page
    assert empty_page.count("data-history-item") == 0

    with patch(
        "gardenhub.services.history.get_recent_sensor_readings",
        side_effect=RuntimeError("sensor source unavailable"),
    ):
        unavailable_history = get_garden_history()
    sensor_category = next(
        category for category in unavailable_history["categories"]
        if category["key"] == "sensors"
    )
    assert sensor_category["available"] is False
    assert sensor_category["empty_title"] == "Sensors history is unavailable."

    print({
        "history_route": response.status_code,
        "weather_history_preserved": True,
        "real_categories": sorted(actual_categories),
        "filters_present": True,
        "empty_state": True,
        "unavailable_state": True,
    })


if __name__ == "__main__":
    run()
