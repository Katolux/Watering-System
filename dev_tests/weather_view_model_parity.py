"""Verify that Workspace and Weather consume the same normalized weather model."""

import gc
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DIRECTORY = tempfile.TemporaryDirectory(prefix="gardenhub-weather-parity-")
TEST_DB = Path(TEST_DIRECTORY.name) / "weather-parity.db"
os.environ["GARDENHUB_DB_PATH"] = str(TEST_DB)

with patch("gardenhub.repositories.weather_repo.should_refresh_weather", return_value=False):
    import app as app_module
from gardenhub.db.connection import get_conn
from gardenhub.repositories.weather_repo import save_current_weather, save_weather_record
from gardenhub.routes import weather_routes
from gardenhub.services.overview import WEATHER_CODES


class WeatherViewModelParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        today = now.date()
        daily_records = (
            {
                "date": today.isoformat(),
                "temp_max": 25.8,
                "temp_min": 14.2,
                "precipitation": 1.7,
                "sunshine": 610.0,
                "daylight": 880.0,
                "wind_max": 18.3,
                "wind_dir": 220.0,
                "weather_code": 2,
            },
            {
                "date": (today + timedelta(days=1)).isoformat(),
                "temp_max": 27.3,
                "temp_min": 15.6,
                "precipitation": 0.2,
                "sunshine": 720.0,
                "daylight": 878.0,
                "wind_max": 14.1,
                "wind_dir": 210.0,
                "weather_code": 1,
            },
            {
                "date": (today + timedelta(days=2)).isoformat(),
                "temp_max": 23.9,
                "temp_min": 13.8,
                "precipitation": 4.4,
                "sunshine": 430.0,
                "daylight": 876.0,
                "wind_max": 21.7,
                "wind_dir": 245.0,
                "weather_code": 61,
            },
        )
        for record in daily_records:
            save_weather_record(record)
        save_current_weather(
            {
                "date": today.isoformat(),
                "timestamp": now.isoformat(),
                "temperature": 19.4,
                "humidity": 73.0,
                "pressure": 1009.0,
                "weather_code": 2,
                "wind_speed": 12.6,
                "wind_direction": 218.0,
            }
        )
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO system_events (
                    timestamp, date, level, source, message
                )
                VALUES (?, ?, 'WARNING', 'weather', ?)
                """,
                (now.isoformat(), today.isoformat(), "Strong wind possible this evening."),
            )

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        TEST_DIRECTORY.cleanup()

    @staticmethod
    def _shared_fields(snapshot):
        current_keys = (
            "temperature",
            "condition",
            "condition_icon",
            "humidity",
            "wind_speed",
            "pressure",
        )
        today_keys = ("temp_max", "temp_min", "precipitation", "condition", "condition_icon")
        forecast_keys = (
            "date",
            "temp_max",
            "temp_min",
            "precipitation",
            "wind_max",
            "condition",
            "condition_icon",
        )
        return {
            "current": {key: snapshot["current"][key] for key in current_keys},
            "today": {key: snapshot["today"][key] for key in today_keys},
            "forecast": [
                {key: day[key] for key in forecast_keys}
                for day in snapshot["forecast"]
            ],
        }

    def test_routes_receive_identical_normalized_weather(self):
        captured = {}

        def capture_workspace(template_name, **context):
            captured["workspace"] = context
            return template_name

        def capture_weather(template_name, **context):
            captured["weather_page"] = context
            return template_name

        with app_module.app.test_request_context("/"):
            with patch.object(app_module, "render_template", side_effect=capture_workspace):
                app_module.index()
            shell_weather = app_module.shell_context()["shell_weather"]

        with app_module.app.test_request_context("/weather"):
            with patch.object(weather_routes, "render_template", side_effect=capture_weather):
                weather_routes.weather()

        workspace_weather = self._shared_fields(captured["workspace"]["weather"])
        weather_page = self._shared_fields(captured["weather_page"]["weather"])
        self.assertEqual(workspace_weather, weather_page)
        self.assertEqual(workspace_weather, self._shared_fields(shell_weather))

    def test_shared_mapping_covers_supported_workspace_icons(self):
        mapped_icons = {icon for _, icon in WEATHER_CODES.values()}
        self.assertTrue(
            {"sun", "cloud-sun", "cloud", "rain", "storm", "snow"}.issubset(
                mapped_icons
            )
        )

    def test_rendered_pages_show_the_same_weather_values(self):
        client = app_module.app.test_client()
        workspace = client.get("/").get_data(as_text=True)
        weather_page = client.get("/weather").get_data(as_text=True)

        shared_values = (
            "Partly cloudy",
            "25.8",
            "14.2",
            "1.7 mm",
            "18.3 km/h",
            "27.3",
        )
        for value in shared_values:
            self.assertIn(value, workspace)
            self.assertIn(value, weather_page)

        workspace_weather_card = workspace.split(
            '<section class="workspace-card weather-panel">', 1
        )[1].split('<section class="workspace-card irrigation-overview-panel">', 1)[0]
        self.assertIn("Today&apos;s Conditions", workspace_weather_card)
        self.assertIn("Stored forecast for today", workspace_weather_card)
        self.assertNotIn("Humidity", workspace_weather_card)
        self.assertNotIn("Pressure", workspace_weather_card)
        self.assertNotIn("19.4", workspace_weather_card)
        self.assertIn("Today&apos;s Conditions", weather_page)
        self.assertNotIn("Current Conditions", weather_page)

        self.assertIn("Strong wind possible this evening.", workspace)
        self.assertNotIn("Stored high", workspace)
        self.assertNotIn("Stored Daily High", workspace)
        self.assertNotIn("Rain recorded", workspace)
        self.assertNotIn("Forecast data is unavailable", workspace)

    def test_global_header_uses_current_weather_on_primary_pages(self):
        client = app_module.app.test_client()
        routes = (
            "/",
            "/planner",
            "/automation",
            "/weather",
            "/automation/plants",
            "/notifications",
            "/weather?tab=history",
        )

        for route in routes:
            with self.subTest(route=route):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                page = response.get_data(as_text=True)
                header = page.split('<header class="app-header">', 1)[1].split(
                    "</header>", 1
                )[0]

                self.assertIn("19.4&deg;C", header)
                self.assertIn("Partly cloudy", header)
                self.assertIn('title="Current weather"', header)
                self.assertNotIn("H 19.4", header)
                self.assertNotIn("25.8&deg;C", header)
                self.assertEqual(header.count('class="weather-context"'), 1)
                self.assertEqual(header.count('class="garden-context"'), 1)
                self.assertEqual(header.count('class="notification-bell"'), 0)
                self.assertEqual(
                    header.count(
                        'class="button button--ghost button--icon notification-bell"'
                    ),
                    1,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
