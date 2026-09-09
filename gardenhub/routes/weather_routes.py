from flask import Blueprint, current_app, render_template, request

from gardenhub.db.connection import is_demo_database
from gardenhub.repositories.weather_repo import should_refresh_weather
from gardenhub.services.garden_context import (
    get_active_garden,
    get_garden_context,
)
from gardenhub.services.weather_view import get_weather_snapshot
from gardenhub.services.weather import fetch_weather_data, refresh_weather


weather_bp = Blueprint(
    "weather",
    __name__,
)

VALID_WEATHER_TABS = {"overview", "forecast", "history", "insights"}


@weather_bp.route("/weather")
def weather():
    demo_mode = is_demo_database()

    active_tab = request.args.get("tab", "overview")
    if active_tab not in VALID_WEATHER_TABS:
        active_tab = "overview"

    garden_context = get_garden_context(
        demo_mode
    )

    active_garden = (
        get_active_garden(garden_context)
        or {}
    )

    location = (
        active_garden.get("location")
        or {}
    )

    current_data = None
    hourly_data = None

    latitude = location.get("latitude")
    longitude = location.get("longitude")
    timezone_name = (
        location.get("timezone")
        or "UTC"
    )

    if (
        not demo_mode
        and latitude is not None
        and longitude is not None
    ):
        try:
            if should_refresh_weather():
                weather_result = refresh_weather(
                    latitude,
                    longitude,
                    timezone_name,
                    force_refresh=True,
                )
            else:
                weather_result = fetch_weather_data(
                    latitude,
                    longitude,
                    timezone_name,
                )

            current_data = weather_result["current"]
            hourly_data = weather_result["hourly"]
        except Exception:
            current_app.logger.exception(
                "Live weather unavailable; rendering stored fallback for "
                "latitude=%s longitude=%s timezone=%s",
                latitude,
                longitude,
                timezone_name,
            )

    weather_snapshot = get_weather_snapshot(
        garden_context=garden_context,
        current_data=current_data,
        hourly_data=hourly_data,
    )

    return render_template(
        "weather.html",
        weather=weather_snapshot,
        garden_context=garden_context,
        active_garden=active_garden,
        demo_mode=demo_mode,
        active_tab=active_tab,
    )
