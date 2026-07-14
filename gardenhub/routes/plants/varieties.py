from flask import request, render_template, redirect, url_for
from gardenhub.repositories.plants_repo import (
    get_all_plants_catalog,
    get_plant_by_id,
    plant_exists,
    variety_exists,
    get_plant_varieties,
    delete_variety,
    insert_rich_variety,
)
from gardenhub.routes.plants import plant_bp
from gardenhub.routes.plants.form_helpers import parse_months


@plant_bp.route("/automation/plants/<plant_id>/varieties/delete-select", methods=["POST"])
def automation_variety_delete_select(plant_id):
    plant = get_plant_by_id(plant_id)
    if not plant:
        return "Plant not found.", 404

    variety_id = request.form.get("variety_id", "").strip().lower()
    varieties = get_plant_varieties(plant_id)

    selected = None
    for v in varieties:
        if v[0] == variety_id:
            selected = v
            break

    if not selected:
        return redirect(url_for("plant.automation_plant_detail", plant_id=plant_id))

    return render_template(
        "automation_variety_confirm_delete.html",
        plant=plant,
        variety=selected
    )

@plant_bp.route("/automation/plants/<plant_id>/varieties/<variety_id>/delete-confirm", methods=["POST"])
def automation_variety_delete_confirm(plant_id, variety_id):
    if not plant_exists(plant_id):
        return "Plant not found.", 404

    if not variety_exists(plant_id, variety_id):
        return "Variety not found.", 404

    delete_variety(plant_id, variety_id)
    return redirect(url_for("plant.automation_plant_detail", plant_id=plant_id))


@plant_bp.route("/automation/plants/add-variety", methods=["GET", "POST"])
def automation_plants_add_variety():
    plants = get_all_plants_catalog()

    if request.method == "POST":
        plant_id = request.form.get("plant_id", "").strip().lower()
        variety_id = request.form.get("variety_id", "").strip().lower()
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()

        sow_indoors_months = parse_months(request.form.get("sow_indoors_months", ""))
        sow_outdoors_months = parse_months(request.form.get("sow_outdoors_months", ""))
        transplant_out_months = parse_months(request.form.get("transplant_out_months", ""))
        harvest_months = parse_months(request.form.get("harvest_months", ""))

        days_to_maturity_min = request.form.get("days_to_maturity_min", "").strip()
        days_to_maturity_max = request.form.get("days_to_maturity_max", "").strip()

        spacing_in_row_cm = request.form.get("spacing_in_row_cm", "").strip()
        spacing_between_rows_cm = request.form.get("spacing_between_rows_cm", "").strip()

        support_needed = request.form.get("support_needed") == "1"
        support_notes = request.form.get("support_notes", "").strip()

        pruning_required = request.form.get("pruning_required") == "1"
        pruning_method = request.form.get("pruning_method", "").strip()
        pruning_notes = request.form.get("pruning_notes", "").strip()

        if not plant_id or not variety_id or not name:
            return render_template(
                "automation_plant_add_variety.html",
                plants=plants,
                error="Plant, variety ID, and variety name are required."
            )

        if not plant_exists(plant_id):
            return render_template(
                "automation_plant_add_variety.html",
                plants=plants,
                error="Parent plant does not exist."
            )

        if variety_exists(plant_id, variety_id):
            return render_template(
                "automation_plant_add_variety.html",
                plants=plants,
                error="This variety already exists for that plant."
            )

        try:
            days_to_maturity_min = int(days_to_maturity_min) if days_to_maturity_min else None
            days_to_maturity_max = int(days_to_maturity_max) if days_to_maturity_max else None
            spacing_in_row_cm = int(spacing_in_row_cm) if spacing_in_row_cm else None
            spacing_between_rows_cm = int(spacing_between_rows_cm) if spacing_between_rows_cm else None
        except ValueError:
            return render_template(
                "automation_plant_add_variety.html",
                plants=plants,
                error="Numeric override fields contain invalid values."
            )

        overrides = {}

        if sow_indoors_months:
            overrides.setdefault("calendar", {}).setdefault("base", {})["sow_indoors"] = {"months": sow_indoors_months}
        if sow_outdoors_months:
            overrides.setdefault("calendar", {}).setdefault("base", {})["sow_outdoors"] = {"months": sow_outdoors_months}
        if transplant_out_months:
            overrides.setdefault("calendar", {}).setdefault("base", {})["transplant_out"] = {"months": transplant_out_months}
        if harvest_months:
            overrides.setdefault("calendar", {}).setdefault("base", {})["harvest"] = {"months": harvest_months}

        if days_to_maturity_min is not None and days_to_maturity_max is not None:
            overrides.setdefault("calendar", {})["days_to_maturity_range"] = [
                days_to_maturity_min,
                days_to_maturity_max
            ]

        if spacing_in_row_cm is not None or spacing_between_rows_cm is not None:
            overrides["spacing_cm"] = {
                "in_row": spacing_in_row_cm,
                "between_rows": spacing_between_rows_cm
            }

        if support_needed or support_notes:
            overrides.setdefault("care", {})["support"] = {
                "needs_support": support_needed,
                "notes": support_notes or None
            }

        if pruning_required or pruning_method or pruning_notes:
            overrides.setdefault("care", {})["pruning"] = {
                "required": pruning_required,
                "method": pruning_method or None,
                "notes": pruning_notes or None
            }

        insert_rich_variety(
            plant_id=plant_id,
            variety_id=variety_id,
            name=name,
            notes=notes,
            overrides=overrides
        )

        return redirect(url_for("plant.automation_plant_detail", plant_id=plant_id))

    return render_template(
        "automation_plant_add_variety.html",
        plants=plants
    )
