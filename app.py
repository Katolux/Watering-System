from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
)
from datetime import datetime, timezone

from get_weather_new import refresh_weather
from historic_weather import get_last_days_weather

from gardenhub.routes.automation_routes import automation_bp
from gardenhub.routes.watering_routes import watering_bp
from gardenhub.routes.sensor_routes import sensor_bp
from gardenhub.routes.plant_routes import plant_bp

from repositories import (
    add_bed,
    assign_plant_to_bed,
    get_all_plants_catalog,
    get_beds_with_plants,
    get_today_moisture_slots,
    should_refresh_weather,
    get_recent_sensor_readings,
    )


from garden_logic import (
    moisture_status,
    overall_bed_status,
)

from watering_engine import (
    daily_average_moisture_from_slots,
)

from python_receiver import receiver_bp
from calibration import raw_to_pct


from db_init import init_all_tables
   # create ALL tables first


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



@app.route("/automation/beds")
def automation_beds():
    beds_with_plants = get_beds_with_plants()
    slots_data = get_today_moisture_slots()

    enriched_beds = []

    for bed_id, active, plant_name, min_m, max_m, base_minutes in beds_with_plants:
        bed_slots = slots_data.get(bed_id, {})
        slot_statuses = {}
        watering_info = None  # optional: load latest decision if you want

        for slot in range(1, 7):
            entry = bed_slots.get(slot)

            raw_value = None
            pct_value = None

            if isinstance(entry, dict):
                raw_value = entry.get("raw")
                pct_value = entry.get("pct")
            elif isinstance(entry, int):
                raw_value = entry
                pct_value = raw_to_pct(raw_value)

            if pct_value is not None and min_m is not None and max_m is not None:
                status = moisture_status(pct_value, min_m, max_m)
            else:
                status = "N/A"

            slot_statuses[slot] = {
                "value": pct_value,
                "raw": raw_value,
                "pct": pct_value,
                "status": status
            }

        summary = overall_bed_status(slot_statuses)
        avg_moisture = daily_average_moisture_from_slots(bed_slots)

        enriched_beds.append({
            "bed_id": bed_id,
            "active": active,
            "plant": plant_name,
            "slots": slot_statuses,
            "summary": summary,
            "avg_moisture": avg_moisture,
            "watering": watering_info,
        })

    return render_template(
        "automation_beds.html",
        beds=enriched_beds,
        plants=get_all_plants_catalog()
    )


@app.route("/automation/beds/add", methods=["POST"])
def automation_beds_add():
    bed_id = request.form.get("bed_id")
    active = request.form.get("active") == "1"

    if bed_id:
        add_bed(bed_id, active)

    return redirect(url_for("automation_beds"))

@app.route("/automation/beds/assign", methods=["POST"])
def automation_beds_assign():
    bed_id = request.form.get("bed_id")
    plant_id = request.form.get("plant_id")
    quantity = request.form.get("quantity")
    variety_id = request.form.get("variety_id") or None

    if bed_id and plant_id:
        assign_plant_to_bed(
            bed_id=bed_id,
            plant_id=plant_id,
            variety_id=variety_id,
            quantity=int(quantity) if quantity else 1,
            planted_at=datetime.now(timezone.utc).isoformat()
        )

    return redirect(url_for("automation_beds"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False) 

