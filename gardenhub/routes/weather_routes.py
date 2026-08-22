from flask import Blueprint, render_template, request

from gardenhub.db.connection import is_demo_database
from gardenhub.services.garden_context import get_garden_context
from gardenhub.services.overview import get_weather_snapshot


weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
def weather():
    active_tab = request.args.get("tab", "overview")
    if active_tab not in {"overview", "forecast", "history", "insights"}:
        active_tab = "overview"
    garden_context = get_garden_context(is_demo_database())
    return render_template(
        "weather.html",
        weather=get_weather_snapshot(garden_context=garden_context),
        active_tab=active_tab,
    )
