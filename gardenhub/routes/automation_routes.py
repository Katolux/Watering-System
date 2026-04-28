from flask import Blueprint, render_template, redirect, url_for

from system_events_repo import get_recent_system_events
from watering_engine import run_watering_engine


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

