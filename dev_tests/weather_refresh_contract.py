"""Focused, isolated checks for the Weather freshness/refresh contract."""

import gc
import os
import sys
import tempfile
import threading
import unittest
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DIRECTORY = tempfile.TemporaryDirectory(
    prefix="gardenhub-weather-refresh-",
    ignore_cleanup_errors=True,
)
TEST_ROOT = Path(TEST_DIRECTORY.name)
os.environ["GARDENHUB_DB_PATH"] = str(TEST_ROOT / "weather-refresh.db")

import app as app_module  # noqa: E402
from gardenhub.db.connection import get_conn  # noqa: E402
from gardenhub.repositories.garden_location_repo import save_garden_location  # noqa: E402
from gardenhub.repositories.weather_repo import (  # noqa: E402
    WEATHER_REFRESH_INTERVAL,
    save_current_weather,
    save_weather_record,
    should_refresh_weather,
)
from gardenhub.routes import weather_routes  # noqa: E402
from gardenhub.services import weather as weather_service  # noqa: E402


def weather_bundle():
    today = date.today()
    current_timestamp = datetime.now(timezone.utc).replace(
        minute=0,
        second=0,
        microsecond=0,
    )
    hourly_dates = pd.date_range(
        start=current_timestamp,
        periods=3,
        freq="h",
    )
    hourly = pd.DataFrame({
        "date": hourly_dates,
        "temperature": [18.7, 19.1, 19.4],
        "humidity": [70.0, 68.0, 66.0],
        "apparent_temperature": [18.2, 18.8, 19.0],
        "precipitation_probability": [10.0, 15.0, 20.0],
        "precipitation": [0.0, 0.0, 0.1],
        "weather_code": [2, 2, 61],
        "cloud_cover": [40.0, 45.0, 60.0],
        "et0": [0.1, 0.1, 0.1],
        "wind_speed": [7.0, 7.5, 8.0],
        "wind_direction": [180.0, 185.0, 190.0],
        "wind_gusts": [12.0, 13.0, 14.0],
        "sunshine_duration": [2700.0, 1800.0, 0.0],
    })
    daily = []
    for offset, high in enumerate((24.6, 25.2)):
        record_date = today + timedelta(days=offset)
        daily.append({
            "date": record_date.isoformat(),
            "weather_code": 2,
            "temp_max": high,
            "temp_min": 13.4 + offset,
            "sunrise": f"{record_date.isoformat()}T06:30:00+00:00",
            "sunset": f"{record_date.isoformat()}T20:15:00+00:00",
            "daylight": 825.0,
            "sunshine": 610.0,
            "precipitation": 0.4,
            "precipitation_probability_max": 20.0,
            "wind_max": 14.0,
            "wind_gusts_max": 22.0,
            "wind_dir": 185.0,
            "et0": 3.2,
        })
    return {
        "timezone": "UTC",
        "current": {
            "date": today.isoformat(),
            "timestamp": current_timestamp.isoformat(),
            "temperature": 19.3,
            "humidity": 70.0,
            "apparent_temperature": 18.8,
            "is_day": 1,
            "precipitation": 0.0,
            "weather_code": 2,
            "cloud_cover": 40.0,
            "pressure": 1012.0,
            "wind_speed": 7.0,
            "wind_direction": 180.0,
            "wind_gusts": 12.0,
        },
        "hourly": hourly,
        "daily": daily,
    }


class WeatherRefreshContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = weather_bundle()
        save_garden_location(
            location_label="Refresh test garden",
            latitude=47.4,
            longitude=9.3,
            timezone_name="UTC",
        )
        save_current_weather(cls.bundle["current"])
        for record in cls.bundle["daily"]:
            save_weather_record(record)
        app_module.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        TEST_DIRECTORY.cleanup()

    def test_valid_and_invalid_weather_tabs_render(self):
        client = app_module.app.test_client()
        with (
            patch.object(weather_routes, "should_refresh_weather", return_value=False),
            patch.object(weather_routes, "fetch_weather_data", return_value=self.bundle),
        ):
            for tab in ("overview", "forecast", "history", "insights"):
                with self.subTest(tab=tab):
                    response = client.get(f"/weather?tab={tab}")
                    self.assertEqual(response.status_code, 200)

            response = client.get("/weather?tab=nonsense")
            page = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                'id="weather-tab-0" aria-selected="true"',
                page,
            )

    def test_current_and_hourly_reach_weather_page(self):
        client = app_module.app.test_client()
        with (
            patch.object(weather_routes, "should_refresh_weather", return_value=False),
            patch.object(weather_routes, "fetch_weather_data", return_value=self.bundle),
        ):
            page = client.get("/weather").get_data(as_text=True)

        self.assertIn("19.3", page)
        self.assertIn("18.7&deg;", page)
        self.assertIn("Hourly Forecast", page)
        self.assertIn('data-sunshine="45.0"', page)
        self.assertIn('data-rain="0.1"', page)

    def test_hourly_chart_uses_24_local_hours_and_crosses_midnight(self):
        from gardenhub.services.weather_view import get_weather_snapshot

        dates = pd.date_range(
            start="2026-08-24 22:00",
            periods=30,
            freq="h",
            tz="Europe/Madrid",
        )
        hourly = pd.DataFrame({
            "date": dates,
            "temperature": [18.0 + index / 10 for index in range(30)],
            "humidity": [65.0] * 30,
            "apparent_temperature": [17.5 + index / 10 for index in range(30)],
            "precipitation_probability": [20.0] * 30,
            "precipitation": [0.2] * 30,
            "weather_code": [2] * 30,
            "cloud_cover": [40.0] * 30,
            "et0": [0.1] * 30,
            "wind_speed": [8.0] * 30,
            "wind_direction": [180.0] * 30,
            "wind_gusts": [12.0] * 30,
            "sunshine_duration": [2700.0] * 30,
        })
        current = dict(self.bundle["current"], timestamp=dates[0].isoformat())

        snapshot = get_weather_snapshot(
            current_data=current,
            hourly_data=hourly,
        )

        self.assertEqual(len(snapshot["hourly"]), 24)
        self.assertEqual(snapshot["hourly"][0]["time"][11:16], "22:00")
        self.assertEqual(snapshot["hourly"][2]["time"][11:16], "00:00")
        self.assertTrue(snapshot["hourly"][2]["is_new_day"])
        self.assertEqual(snapshot["hourly"][-1]["time"][11:16], "21:00")
        self.assertEqual(snapshot["hourly"][0]["sunshine_minutes"], 45.0)

    def test_stale_weather_uses_refresh_service_bundle(self):
        client = app_module.app.test_client()
        with (
            patch.object(weather_routes, "should_refresh_weather", return_value=True),
            patch.object(weather_routes, "refresh_weather", return_value=self.bundle) as refresh,
            patch.object(weather_routes, "fetch_weather_data") as fetch,
        ):
            response = client.get("/weather")

        self.assertEqual(response.status_code, 200)
        refresh.assert_called_once_with(47.4, 9.3, "UTC", force_refresh=True)
        fetch.assert_not_called()

    def test_provider_failure_renders_stored_fallback(self):
        client = app_module.app.test_client()
        app_module.app.logger.disabled = True
        try:
            with (
                patch.object(weather_routes, "should_refresh_weather", return_value=False),
                patch.object(
                    weather_routes,
                    "fetch_weather_data",
                    side_effect=RuntimeError("provider unavailable"),
                ),
            ):
                response = client.get("/weather")
        finally:
            app_module.app.logger.disabled = False

        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("19.3", page)
        self.assertIn("Hourly forecast is not available right now.", page)

    def test_manual_refresh_remains_forced(self):
        client = app_module.app.test_client()
        with patch.object(app_module, "refresh_weather", return_value=self.bundle) as refresh:
            response = client.post(
                "/refresh_weather",
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        refresh.assert_called_once_with(47.4, 9.3, "UTC", force_refresh=True)

    def test_freshness_threshold_is_one_hour(self):
        self.assertEqual(WEATHER_REFRESH_INTERVAL, timedelta(hours=1))
        stale_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
        with get_conn() as conn:
            conn.execute("UPDATE weather_data SET timestamp = ?", (stale_timestamp,))
        self.assertTrue(should_refresh_weather())

        fresh_timestamp = datetime.now(timezone.utc).isoformat()
        with get_conn() as conn:
            conn.execute("UPDATE weather_data SET timestamp = ?", (fresh_timestamp,))
        self.assertFalse(should_refresh_weather())

    def test_refresh_persists_current_and_daily_but_not_hourly(self):
        with patch.object(
            weather_service,
            "fetch_weather_data",
            return_value=self.bundle,
        ) as fetch:
            result = weather_service.refresh_weather(
                47.4,
                9.3,
                "UTC",
                force_refresh=True,
            )

        self.assertIs(result, self.bundle)
        fetch.assert_called_once_with(47.4, 9.3, "UTC", force_refresh=True)

        with get_conn() as conn:
            current = conn.execute(
                "SELECT current_temperature FROM weather_data WHERE date = ?",
                (date.today().isoformat(),),
            ).fetchone()
            daily_count = conn.execute(
                "SELECT COUNT(*) FROM weather_data WHERE temp_max IS NOT NULL"
            ).fetchone()[0]
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(weather_data)").fetchall()
            }
        self.assertEqual(current[0], self.bundle["current"]["temperature"])
        self.assertEqual(daily_count, len(self.bundle["daily"]))
        self.assertFalse(any(column.startswith("hourly_") for column in columns))

    def test_browser_refresh_is_hourly_and_preserves_the_tab(self):
        source = (ROOT / "static" / "js" / "weather.js").read_text(encoding="utf-8")
        self.assertIn("60 * 60 * 1000", source)
        self.assertIn("window.location.reload()", source)
        self.assertIn("window.history.replaceState", source)

    def test_force_refresh_overwrites_the_normal_request_cache(self):
        class CounterHandler(BaseHTTPRequestHandler):
            count = 0

            def do_GET(self):
                type(self).count += 1
                body = str(type(self).count).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), CounterHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/weather"

        try:
            with patch.object(
                weather_service,
                "WEATHER_CACHE_PATH",
                TEST_ROOT / "provider-cache",
            ):
                with weather_service._weather_session() as session:
                    first = session.get(url)
                with weather_service._weather_session() as session:
                    forced = session.get(url, force_refresh=True)
                with weather_service._weather_session() as session:
                    normal = session.get(url)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(first.text, "1")
        self.assertEqual(forced.text, "2")
        self.assertEqual(normal.text, "2")
        self.assertTrue(normal.from_cache)


if __name__ == "__main__":
    unittest.main(verbosity=2)
