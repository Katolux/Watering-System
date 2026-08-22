"""Shared active-garden context without inventing backend persistence.

The current database is a single-garden schema: beds, sensors, plantings, and
weather records have no garden foreign key.  This module keeps that limitation
visible while giving the frontend one contract that can later be populated by a
real gardens API.
"""

from gardenhub.demo_config import DEMO_GARDEN


# Temporary compatibility only. Remove this fallback once the gardens API
# supplies address_label, latitude, and longitude for the active garden.
TEMPORARY_GARDEN_LOCATION_FALLBACK = {
    "address_label": "Temporary weather location",
    "latitude": 47.4455,
    "longitude": 9.342,
    "timezone": "UTC",
    "source": "temporary_fallback",
    "persisted": False,
}


def get_garden_context(demo_mode=False):
    """Return the single-garden context exposed by the current application.

    The list shape and active_garden_id are intentional: when the backend grows
    garden ownership, this function can return multiple records without changing
    the shell, Workspace, or location controls.
    """

    garden_id = "demo-garden" if demo_mode else "local-garden"
    garden_name = DEMO_GARDEN["name"] if demo_mode else "Garden"
    garden = {
        "id": garden_id,
        "name": garden_name,
        "location": dict(TEMPORARY_GARDEN_LOCATION_FALLBACK),
    }
    return {
        "active_garden_id": garden_id,
        "gardens": [garden],
        "persistence": "browser_session_only",
        "backend_supports_multiple_gardens": False,
    }


def get_active_garden(garden_context):
    active_id = garden_context.get("active_garden_id")
    gardens = garden_context.get("gardens") or []
    return next(
        (garden for garden in gardens if garden.get("id") == active_id),
        gardens[0] if gardens else None,
    )


def get_weather_coordinates(garden_context):
    """Resolve weather coordinates exclusively through the active garden."""

    garden = get_active_garden(garden_context) or {}
    location = garden.get("location") or TEMPORARY_GARDEN_LOCATION_FALLBACK
    return {
        "latitude": float(location["latitude"]),
        "longitude": float(location["longitude"]),
        "timezone": location.get("timezone") or "UTC",
    }
