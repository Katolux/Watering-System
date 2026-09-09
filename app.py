from pathlib import Path
from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    request,
    url_for,
)

from gardenhub.services.weather import refresh_weather
from gardenhub.services.geocoding import (
    search_location,
    resolve_timezone,
)
from gardenhub.services.garden_context import (
    get_active_garden,
    get_garden_context,
    get_weather_coordinates,
)
from gardenhub.routes.automation_routes import automation_bp
from gardenhub.routes.watering_routes import watering_bp
from gardenhub.routes.sensor_routes import sensor_bp
from gardenhub.routes.plants import plant_bp
from gardenhub.routes.weather_routes import weather_bp
from gardenhub.routes.planner_routes import planner_bp
from gardenhub.routes.notification_routes import notifications_bp

from gardenhub.routes.receiver_routes import receiver_bp

from gardenhub.db.initialization import init_all_tables
from gardenhub.db.connection import is_demo_database
from gardenhub.demo_config import DEMO_GARDEN
from gardenhub.services.overview import (
    get_garden_snapshot,
    get_planner_state,
)
from gardenhub.services.weather_view import get_weather_snapshot
from gardenhub.repositories.system_events_repo import get_recent_system_events
from gardenhub.repositories.garden_location_repo import save_garden_location
from gardenhub.repositories.plants_repo import get_all_plants_catalog
from gardenhub.services.notifications import (
    get_notification_feed,
    unavailable_notification_feed,
)
from gardenhub.services.history import get_garden_history
from gardenhub.repositories.weather_repo import (
    should_refresh_weather,
)
from seeding.plant_seeder import seed_all_plants



app = Flask(__name__)
app.register_blueprint(receiver_bp)
app.register_blueprint(automation_bp)
app.register_blueprint(watering_bp)
app.register_blueprint(sensor_bp)
app.register_blueprint(plant_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(planner_bp)
app.register_blueprint(notifications_bp)

init_all_tables()

if not get_all_plants_catalog():
    seed_all_plants(str(Path(__file__).resolve().parent / "plants"))

try:
    if not is_demo_database() and should_refresh_weather():
        startup_garden_context = get_garden_context(False)
        startup_coordinates = get_weather_coordinates(startup_garden_context)
        refresh_weather(
            startup_coordinates["latitude"],
            startup_coordinates["longitude"],
            startup_coordinates["timezone"],
            force_refresh=True,
        )
except Exception as e:
    print(f"Startup weather refresh skipped: {e}")


@app.context_processor
def shell_context():
    demo_mode = is_demo_database()
    garden_context = get_garden_context(demo_mode)
    try:
        shell_notifications = get_notification_feed(limit=100, preview_limit=4)
    except Exception:
        shell_notifications = unavailable_notification_feed()
    return {
        "demo_mode": demo_mode,
        "demo_garden": DEMO_GARDEN if demo_mode else None,
        "garden_context": garden_context,
        "active_garden": get_active_garden(garden_context),
        "shell_weather": get_weather_snapshot(garden_context=garden_context),
        "shell_notifications": shell_notifications,
    }


@app.route("/")
def index():
    system_events = get_recent_system_events(5)
    garden_context = get_garden_context(is_demo_database())

    return render_template(
        "index.html",
        weather=get_weather_snapshot(garden_context=garden_context),
        system_events=system_events,
        garden=get_garden_snapshot(),
        planner_state=get_planner_state(garden_context=garden_context),
    )

@app.route("/refresh_weather", methods=["POST"])
def refresh_weather_route():
    wants_json = request.accept_mimetypes.best == "application/json"
    if is_demo_database():
        if wants_json:
            return jsonify({
                "ok": False,
                "error": "Live weather refresh is unavailable for demo data.",
            }), 409
        return redirect(url_for("weather.weather"))

    garden_context = get_garden_context(False)
    coordinates = get_weather_coordinates(garden_context)
    try:
        refresh_weather(
            coordinates["latitude"],
            coordinates["longitude"],
            coordinates["timezone"],
            force_refresh=True,
        )
    except Exception:
        app.logger.exception(
            "Manual weather refresh failed for latitude=%s longitude=%s timezone=%s",
            coordinates["latitude"],
            coordinates["longitude"],
            coordinates["timezone"],
        )
        if wants_json:
            return jsonify({
                "ok": False,
                "error": "The weather provider could not be refreshed.",
            }), 502
        raise

    if wants_json:
        snapshot = get_weather_snapshot(garden_context=garden_context)
        return jsonify({
            "ok": True,
            "updated_label": snapshot["current"]["updated_label"],
        })
    return redirect(url_for("weather.weather"))

@app.route("/garden-location", methods=["POST"])
def save_garden_location_route():
    data = request.get_json(silent=True) or {}

    location_label = data.get("location_label")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({
            "ok": False,
            "error": "Latitude and longitude are required.",
        }), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "error": "Latitude and longitude must be valid numbers.",
        }), 400

    if not -90 <= latitude <= 90:
        return jsonify({
            "ok": False,
            "error": "Latitude must be between -90 and 90.",
        }), 400

    if not -180 <= longitude <= 180:
        return jsonify({
            "ok": False,
            "error": "Longitude must be between -180 and 180.",
        }), 400

    try:
        timezone_name = resolve_timezone(
            latitude,
            longitude,
        )
    except Exception:
        app.logger.exception(
            "Timezone resolution failed for latitude=%s longitude=%s",
            latitude,
            longitude,
        )

        return jsonify({
            "ok": False,
            "error": "The timezone for this location could not be determined.",
        }), 502

    save_garden_location(
        location_label=location_label,
        latitude=latitude,
        longitude=longitude,
        timezone_name=timezone_name,
    )

    return jsonify({
        "ok": True,
        "location": {
            "location_label": location_label,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone_name,
        },
    })

@app.route("/garden-location/search")
def search_garden_location():
    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify({
            "ok": False,
            "error": "Enter a location to search.",
        }), 400

    try:
        results = search_location(query)

    except Exception:
        app.logger.exception(
            "Garden location search failed for query=%s",
            query,
        )

        return jsonify({
            "ok": False,
            "error": "Location search is currently unavailable.",
        }), 502

    return jsonify({
        "ok": True,
        "results": results,
    })

@app.route("/history")
def history():
    return render_template("history.html", history=get_garden_history())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False) 
