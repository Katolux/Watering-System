from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
)

from get_weather_new import refresh_weather
from historic_weather import get_last_days_weather

from gardenhub.routes.automation_routes import automation_bp
from gardenhub.routes.watering_routes import watering_bp
from gardenhub.routes.sensor_routes import sensor_bp
from gardenhub.routes.plant_routes import plant_bp

from repositories import (
    should_refresh_weather,
    get_recent_sensor_readings,
    )


from python_receiver import receiver_bp

from db_init import init_all_tables



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
    return render_template("index.html")

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

