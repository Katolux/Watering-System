from flask import Blueprint, request, render_template, redirect, url_for

from repositories import(
    get_all_sensors,
    add_sensor,
    assign_sensor_to_bed,
    get_all_beds,
)

sensor_bp = Blueprint("sensor", __name__)


@sensor_bp.route("/automation/sensors")
def automation_sensors():
    sensors = get_all_sensors()
    beds = get_all_beds()
    return render_template(
        "automation_sensors.html",
        sensors=sensors,
        beds=beds
    )

@sensor_bp.route("/automation/sensors/add", methods=["POST"])
def automation_sensors_add():
    sensor_id = request.form.get("sensor_id")
    active = request.form.get("active") == "1"

    if sensor_id:
        add_sensor(sensor_id, active)

    return redirect(url_for("sensor.automation_sensors"))

@sensor_bp.route("/automation/sensors/assign", methods=["POST"])
def automation_sensors_assign():
    sensor_id = request.form.get("sensor_id")
    bed_id = request.form.get("bed_id")

    if sensor_id and bed_id:
        assign_sensor_to_bed(sensor_id, bed_id)

    return redirect(url_for("sensor.automation_sensors"))