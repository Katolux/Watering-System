from flask import Blueprint, current_app, jsonify, render_template, request

from gardenhub.db.connection import is_demo_database
from gardenhub.services.garden_context import get_garden_context
from gardenhub.services.overview import (
    get_garden_snapshot,
    get_planner_catalog,
    get_planner_state,
)
from gardenhub.services.planner_layout import (
    PlannerLayoutValidationError,
    load_planner_layout,
    save_planner_layout,
)


planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/planner")
def planner():
    catalog = get_planner_catalog()
    garden_context = get_garden_context(is_demo_database())
    return render_template(
        "planner.html",
        garden=get_garden_snapshot(),
        catalog=catalog,
        planner_state=get_planner_state(catalog, garden_context=garden_context),
    )


def _active_garden_id():
    context = get_garden_context(is_demo_database())
    return context["active_garden_id"]


@planner_bp.route("/api/planner/layout", methods=["GET"])
def planner_layout_get():
    garden_id = _active_garden_id()
    layout = load_planner_layout(garden_id)
    if layout is None:
        return jsonify({"ok": True, "planExists": False, "gardenId": garden_id})
    return jsonify({
        "ok": True,
        "planExists": True,
        "gardenId": garden_id,
        "version": layout["schema_version"],
        "garden": layout["garden"],
        "objects": layout["objects"],
        "updatedAt": layout["updated_at"],
    })


@planner_bp.route("/api/planner/layout", methods=["PUT"])
def planner_layout_put():
    try:
        payload = request.get_json(force=False, silent=True)
        saved = save_planner_layout(_active_garden_id(), payload)
    except PlannerLayoutValidationError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception:
        current_app.logger.exception("Planner layout save failed")
        return jsonify({"ok": False, "error": "The Planner layout could not be saved."}), 500
    return jsonify({"ok": True, **saved})
