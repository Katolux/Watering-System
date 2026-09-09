"""Focused, isolated checks for compact garden-location labels."""

import gc
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DIRECTORY = tempfile.TemporaryDirectory(
    prefix="gardenhub-location-label-",
    ignore_cleanup_errors=True,
)
os.environ["GARDENHUB_DB_PATH"] = str(
    Path(TEST_DIRECTORY.name) / "location-label.db"
)

import app as app_module  # noqa: E402
from gardenhub.repositories.garden_location_repo import get_garden_location  # noqa: E402
from gardenhub.routes import weather_routes  # noqa: E402
from gardenhub.services.garden_context import (  # noqa: E402
    get_active_garden,
    get_garden_context,
    get_weather_coordinates,
)
from gardenhub.services.geocoding import search_location, short_location_label  # noqa: E402


ENGELBURG_RESULT = {
    "display_name": (
        "51, St. Gallerstrasse, Engelburg, Strick, Engelburg, Gaiserwald, "
        "Wahlkreis St. Gallen, St. Gallen, 9032, "
        "Schweiz/Suisse/Svizzera/Svizra"
    ),
    "lat": "47.4406659",
    "lon": "9.348008",
    "address": {
        "house_number": "51",
        "road": "St. Gallerstrasse",
        "village": "Engelburg",
        "municipality": "Gaiserwald",
        "county": "Wahlkreis St. Gallen",
        "state": "St. Gallen",
        "postcode": "9032",
        "country": "Schweiz/Suisse/Svizzera/Svizra",
        "country_code": "ch",
    },
}


class GardenLocationLabelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        TEST_DIRECTORY.cleanup()

    def test_structured_engelburg_address_produces_short_label(self):
        self.assertEqual(
            short_location_label(ENGELBURG_RESULT),
            "Engelburg, St. Gallen",
        )

    def test_search_returns_short_label_with_original_coordinates(self):
        response = Mock()
        response.json.return_value = [ENGELBURG_RESULT]
        response.raise_for_status.return_value = None

        with patch("gardenhub.services.geocoding.requests.get", return_value=response):
            results = search_location("Engelburg")

        self.assertEqual(results, [{
            "label": "Engelburg, St. Gallen",
            "latitude": 47.4406659,
            "longitude": 9.348008,
        }])

    def test_label_fallbacks_never_return_empty(self):
        self.assertEqual(
            short_location_label({"address": {"town": "Gossau"}}),
            "Gossau",
        )
        self.assertEqual(
            short_location_label({"display_name": "Fallback place"}),
            "Fallback place",
        )
        self.assertEqual(short_location_label({}), "Selected garden location")

    def test_save_reload_and_weather_header_keep_short_label(self):
        client = app_module.app.test_client()
        with patch.object(app_module, "resolve_timezone", return_value="Europe/Zurich"):
            response = client.post("/garden-location", json={
                "location_label": "Engelburg, St. Gallen",
                "latitude": 47.4406659,
                "longitude": 9.348008,
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["location"]["location_label"], "Engelburg, St. Gallen")

        stored = get_garden_location()
        self.assertEqual(stored["location_label"], "Engelburg, St. Gallen")
        self.assertEqual(stored["latitude"], 47.4406659)
        self.assertEqual(stored["longitude"], 9.348008)
        self.assertEqual(stored["timezone"], "Europe/Zurich")

        garden_context = get_garden_context(False)
        active_garden = get_active_garden(garden_context)
        self.assertEqual(
            active_garden["location"]["address_label"],
            "Engelburg, St. Gallen",
        )
        self.assertEqual(get_weather_coordinates(garden_context), {
            "latitude": 47.4406659,
            "longitude": 9.348008,
            "timezone": "Europe/Zurich",
        })

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
                page = client.get("/weather").get_data(as_text=True)
        finally:
            app_module.app.logger.disabled = False

        self.assertIn(
            '<span class="weather-location__label">Engelburg, St. Gallen</span>',
            page,
        )
        self.assertIn(
            'data-active-garden-location>Engelburg, St. Gallen</small>',
            page,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
