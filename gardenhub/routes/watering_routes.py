from flask import Blueprint, render_template, redirect, url_for, request

from repositories import (
    get_beds_with_plants,
    get_recent_watering_events,
    get_latest_watering_decision,
    log_watering_event,
)

from watering_engine import run_watering_engine


watering_bp = Blueprint("watering", __name__)


@watering_bp.route("/watering")
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


@watering_bp.route("/water_now", methods=["POST"])
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

    return redirect(url_for("watering.watering"))
