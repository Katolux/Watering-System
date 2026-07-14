from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
)

from gardenhub.services.weather import refresh_weather
from gardenhub.routes.automation_routes import automation_bp
from gardenhub.routes.watering_routes import watering_bp
from gardenhub.routes.sensor_routes import sensor_bp
from gardenhub.routes.plants import plant_bp

from gardenhub.repositories.sensors_repo import get_recent_sensor_readings


from gardenhub.routes.receiver_routes import receiver_bp

from gardenhub.db.initialization import init_all_tables
from gardenhub.repositories.system_events_repo import get_recent_system_events
from gardenhub.repositories.weather_repo import (
    get_last_days_weather,
    get_today_weather_record,
    should_refresh_weather,
)



app = Flask(__name__)
app.register_blueprint(receiver_bp)
app.register_blueprint(automation_bp)
app.register_blueprint(watering_bp)
app.register_blueprint(sensor_bp)
app.register_blueprint(plant_bp)

init_all_tables()

try:
    if should_refresh_weather():
        refresh_weather()
except Exception as e:
    print(f"Startup weather refresh skipped: {e}")


@app.route("/")
def index():
    latest_weather = get_today_weather_record()
    system_events = get_recent_system_events(5)

    return render_template(
        "index.html",
        latest_weather=latest_weather,
        system_events=system_events
    )

@app.route("/refresh_weather", methods=["POST"])
def refresh_weather_route():
    refresh_weather()
    return redirect(url_for("index"))


@app.route("/history")
def history():
    weather = get_last_days_weather(days=10)
    readings = get_recent_sensor_readings(limit=200)
    return render_template("history.html", weather=weather, readings=readings)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False) 

