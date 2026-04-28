from flask import Blueprint, render_template, redirect, url_for, request
from datetime import datetime, timezone
from system_events_repo import get_recent_system_events
from watering_engine import run_watering_engine
from calibration import raw_to_pct

from repositories import (
    add_bed,
    assign_plant_to_bed,
    get_all_plants_catalog,
    get_beds_with_plants,
    get_today_moisture_slots,
    get_latest_watering_decision,
    )


from garden_logic import (
    moisture_status,
    overall_bed_status,
)

from watering_engine import (
    daily_average_moisture_from_slots,
)

automation_bp = Blueprint("automation", __name__)


@automation_bp.route("/automation")
def automation():
    return render_template(
        "automation.html",
        system_events=get_recent_system_events(20)
    )


@automation_bp.route("/automation/run_watering_engine", methods=["POST"])
def automation_run_watering_engine():
    run_watering_engine()
    return redirect(url_for("automation.automation"))

@automation_bp.route("/automation/beds")
def automation_beds():
    beds_with_plants = get_beds_with_plants()
    slots_data = get_today_moisture_slots()

    enriched_beds = []

    for bed_id, active, plant_name, min_m, max_m, base_minutes in beds_with_plants:
        bed_slots = slots_data.get(bed_id, {})
        slot_statuses = {}
        latest_decision = get_latest_watering_decision(bed_id)

        if latest_decision:
            watering_info = {
                "minutes": latest_decision[0],
                "soil_factor": latest_decision[1],
                "temp_factor": latest_decision[2],
                "rain_factor": latest_decision[3],
                "timestamp": latest_decision[4],
            }
        else:
            watering_info = None

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


@automation_bp.route("/automation/beds/add", methods=["POST"])
def automation_beds_add():
    bed_id = request.form.get("bed_id")
    active = request.form.get("active") == "1"

    if bed_id:
        add_bed(bed_id, active)

    return redirect(url_for("automation.automation_beds"))

@automation_bp.route("/automation/beds/assign", methods=["POST"])
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

    return redirect(url_for("automation.automation_beds"))
