"""Shared active-garden context for the current single-garden application."""

from gardenhub.demo_config import DEMO_GARDEN
from gardenhub.repositories.garden_location_repo import get_garden_location


def get_garden_context(demo_mode=False):
    """Return the current single-garden context."""

    garden_id = "demo-garden" if demo_mode else "local-garden"
    garden_name = DEMO_GARDEN["name"] if demo_mode else "Garden"

    if demo_mode:
        location = {
            "address_label": "Demo garden location",
            "latitude": 47.4455,
            "longitude": 9.342,
            "timezone": "Europe/Zurich",
            "source": "demo",
            "persisted": False,
        }
    else:
        saved_location = get_garden_location()

        if saved_location:
            location = {
                "address_label": saved_location["location_label"],
                "latitude": saved_location["latitude"],
                "longitude": saved_location["longitude"],
                "timezone": saved_location["timezone"],
                "source": "saved",
                "persisted": True,
            }
        else:
            location = {
                "address_label": "Location unavailable",
                "latitude": None,
                "longitude": None,
                "timezone": None,
                "source": "missing",
                "persisted": False,
            }

    garden = {
        "id": garden_id,
        "name": garden_name,
        "location": location,
    }

    return {
        "active_garden_id": garden_id,
        "gardens": [garden],
        "persistence": "backend" if not demo_mode else "demo",
        "backend_supports_multiple_gardens": False,
    }


def get_active_garden(garden_context):
    active_id = garden_context.get("active_garden_id")
    gardens = garden_context.get("gardens") or []

    return next(
        (
            garden
            for garden in gardens
            if garden.get("id") == active_id
        ),
        gardens[0] if gardens else None,
    )


def get_weather_coordinates(garden_context):
    """Return saved coordinates for the active garden."""

    garden = get_active_garden(garden_context) or {}
    location = garden.get("location") or {}

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        raise ValueError(
            "Garden location has not been configured."
        )

    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "timezone": location.get("timezone") or "UTC",
    }