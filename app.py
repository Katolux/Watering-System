from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request
)

from get_weather_new import refresh_weather
from historic_weather import get_last_days_weather

from repositories import (
    add_bed,
    get_all_beds,
    add_plant,
    get_all_plants,
    assign_plant_to_bed,
    get_beds_with_plants,
    get_today_moisture_slots,
    get_all_sensors,
    add_sensor,
    assign_sensor_to_bed,
    log_watering_event,
    should_refresh_weather,
    get_recent_sensor_readings,
    get_recent_watering_events,
    get_latest_watering_decision,

)

from garden_logic import (
    moisture_status,
    overall_bed_status,
)

from watering_engine import (
    run_watering_engine,
    daily_average_moisture_from_slots,
)

from system_events_repo import get_recent_system_events
from python_receiver import receiver_bp
from calibration import raw_to_pct


from db_init import init_all_tables
   # create ALL tables first


app = Flask(__name__)
app.register_blueprint(receiver_bp)
if should_refresh_weather():
    refresh_weather()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/refresh_weather", methods=["POST"])
def refresh_weather_route():
    refresh_weather()
    return redirect(url_for("index"))


@app.route("/watering")
def watering():
    beds = get_beds_with_plants()
    latest_by_bed = {}
    for bed_id, active, plant_name, min_m, max_m, base_minutes in beds:
        latest_by_bed[bed_id] = get_latest_watering_decision(bed_id)

    events = get_recent_watering_events(limit=100)

    return render_template(
        "watering.html",
        beds=beds,
        latest_by_bed=latest_by_bed,
        events=events
    )



@app.route("/history")
def history():
    weather = get_last_days_weather(days=10)
    readings = get_recent_sensor_readings(limit=200)
    return render_template("history.html", weather=weather, readings=readings)



@app.route("/automation")
def automation():
    return render_template(
        "automation.html",
        system_events=get_recent_system_events(20)
    )


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
            if isinstance(entry, dict):
                raw_value = entry.get("raw")
            elif isinstance(entry, int):
                raw_value = entry

            if raw_value is not None and min_m is not None and max_m is not None:
                status = moisture_status(raw_value, min_m, max_m)
            else:
                status = "unknown"

            slot_statuses[slot] = {
                "value": raw_value,
                "pct": raw_to_pct(raw_value) if raw_value is not None else None,
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
        plants=get_all_plants()
    )


@app.route("/automation/beds/add", methods=["POST"])
def automation_beds_add():
    bed_id = request.form.get("bed_id")
    active = request.form.get("active") == "1"

    if bed_id:
        add_bed(bed_id, active)

    return redirect(url_for("automation_beds"))

@app.route("/automation/plants")
def automation_plants():
    plants = get_all_plants()
    return render_template("automation_plants.html", plants=plants)


@app.route("/automation/beds/assign", methods=["POST"])
def automation_beds_assign():
    bed_id = request.form.get("bed_id")
    plant_id = request.form.get("plant_id")
    quantity = request.form.get("quantity")

    if bed_id and plant_id:
        # get plant name from DB
        plants = get_all_plants()
        plant_name = None
        for pid, name, *_ in plants:
            if pid == plant_id:
                plant_name = name
                break

        if plant_name:
            assign_plant_to_bed(
                bed_id,
                plant_id,
                plant_name,
                int(quantity) if quantity else 1
            )

    return redirect(url_for("automation_beds"))



@app.route("/automation/sensors")
def automation_sensors():
    sensors = get_all_sensors()
    beds = get_all_beds()
    return render_template(
        "automation_sensors.html",
        sensors=sensors,
        beds=beds
    )

@app.route("/automation/sensors/add", methods=["POST"])
def automation_sensors_add():
    sensor_id = request.form.get("sensor_id")
    active = request.form.get("active") == "1"

    if sensor_id:
        add_sensor(sensor_id, active)

    return redirect(url_for("automation_sensors"))

@app.route("/automation/sensors/assign", methods=["POST"])
def automation_sensors_assign():
    sensor_id = request.form.get("sensor_id")
    bed_id = request.form.get("bed_id")

    if sensor_id and bed_id:
        assign_sensor_to_bed(sensor_id, bed_id)

    return redirect(url_for("automation_sensors"))

@app.route("/water_now", methods=["POST"])
def water_now():
    bed_id = request.form.get("bed_id")
    minutes = request.form.get("minutes")

    if bed_id and minutes:
        log_watering_event(
            bed_id=bed_id,
            minutes=int(minutes),
            mode="manual",
            note="Triggered from web UI"
        )

        print(f"WATER NOW → {bed_id} for {minutes} min")

    return redirect(url_for("automation_beds"))

@app.route("/admin/run_watering_engine")
def run_engine_now():
    run_watering_engine()
    return "Watering decisions calculated"

@app.route("/automation/run_watering_engine")
def automation_run_watering_engine():
    run_watering_engine()
    return redirect(url_for("automation"))



if __name__ == "__main__":
    init_all_tables()  # create ALL tables first
    app.run(host="0.0.0.0", port=5000, debug=False)

