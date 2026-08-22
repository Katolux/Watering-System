"""Targeted contract checks for the Workspace garden-context refinement."""

import inspect
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gardenhub.services.garden_context import (
    TEMPORARY_GARDEN_LOCATION_FALLBACK,
    get_garden_context,
    get_weather_coordinates,
)
from gardenhub.services.weather import refresh_weather


class WorkspaceGardenContextSmokeTest(unittest.TestCase):
    def test_weather_service_requires_dynamic_coordinates(self):
        signature = inspect.signature(refresh_weather)
        self.assertEqual(list(signature.parameters)[:2], ["latitude", "longitude"])
        self.assertIs(signature.parameters["latitude"].default, inspect.Parameter.empty)
        self.assertIs(signature.parameters["longitude"].default, inspect.Parameter.empty)

        context = get_garden_context(False)
        self.assertEqual(
            get_weather_coordinates(context),
            {
                "latitude": TEMPORARY_GARDEN_LOCATION_FALLBACK["latitude"],
                "longitude": TEMPORARY_GARDEN_LOCATION_FALLBACK["longitude"],
                "timezone": TEMPORARY_GARDEN_LOCATION_FALLBACK["timezone"],
            },
        )

    def test_workspace_exposes_real_context_and_clean_empty_state(self):
        workspace_template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        shell_template = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")

        self.assertNotIn("workspace-search", workspace_template)
        self.assertNotIn("Garden not configured", workspace_template)
        self.assertNotIn("Schematic placeholder", workspace_template)
        self.assertNotIn("renderer unavailable", workspace_template)
        self.assertNotIn("data-workspace-plan-state", workspace_template)
        self.assertNotIn("data-workspace-garden-scene", workspace_template)
        self.assertNotIn("2D Map", workspace_template)
        self.assertIn("No garden plan available", workspace_template)
        self.assertIn("Planner layout ready", workspace_template)
        self.assertIn("A richer Living Garden view", workspace_template)
        self.assertIn("Open Planner", workspace_template)
        self.assertIn("data-garden-context", shell_template)
        self.assertIn("data-location-dialog", shell_template)
        self.assertIn("Use my current location", shell_template)


if __name__ == "__main__":
    unittest.main(verbosity=2)
