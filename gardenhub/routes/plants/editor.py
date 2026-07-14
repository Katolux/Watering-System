from flask import request, render_template, redirect, url_for
import json
from gardenhub.repositories.plants_repo import (
    get_plant_by_id,
    plant_exists,
    insert_rich_plant,
    update_rich_plant,
)
from gardenhub.routes.plants import plant_bp
from gardenhub.routes.plants.form_helpers import (
    derive_watering_defaults,
    parse_months,
    plant_to_form_data,
)


@plant_bp.route("/automation/plants/add", methods=["GET", "POST"])
def add_plant():
    if request.method == "POST":
        plant_id = request.form.get("plant_id", "").strip().lower()
        name = request.form.get("name", "").strip()
        scientific_name = request.form.get("scientific_name", "").strip()
        category = request.form.get("category", "").strip()
        family = request.form.get("family", "").strip()

        emoji = request.form.get("emoji", "").strip()
        icon_key = request.form.get("icon_key", "").strip()
        photo_key = request.form.get("photo_key", "").strip()

        spacing_in_row_cm = request.form.get("spacing_in_row_cm", "").strip()
        spacing_between_rows_cm = request.form.get("spacing_between_rows_cm", "").strip()

        root_depth_min_cm = request.form.get("root_depth_min_cm", "").strip()
        root_depth_max_cm = request.form.get("root_depth_max_cm", "").strip()
        root_type = request.form.get("root_type", "").strip()

        water_need = request.form.get("water_need", "").strip().lower()
        irrigation_sensitivity = request.form.get("irrigation_sensitivity", "").strip().lower()
        mulch_helpful = request.form.get("mulch_helpful") == "1"

        soil_drainage = request.form.get("soil_drainage", "").strip()
        soil_ph_min = request.form.get("soil_ph_min", "").strip()
        soil_ph_max = request.form.get("soil_ph_max", "").strip()
        soil_notes = request.form.get("soil_notes", "").strip()

        feeder = request.form.get("feeder", "").strip()
        nutrition_emphasis = request.form.get("nutrition_emphasis", "").strip()
        nutrition_notes = request.form.get("nutrition_notes", "").strip()

        sow_indoors_months = parse_months(request.form.get("sow_indoors_months", ""))
        sow_outdoors_months = parse_months(request.form.get("sow_outdoors_months", ""))
        transplant_out_months = parse_months(request.form.get("transplant_out_months", ""))
        harvest_months = parse_months(request.form.get("harvest_months", ""))

        days_to_maturity_min = request.form.get("days_to_maturity_min", "").strip()
        days_to_maturity_max = request.form.get("days_to_maturity_max", "").strip()

        support_needed = request.form.get("support_needed") == "1"
        support_notes = request.form.get("support_notes", "").strip()

        pruning_required = request.form.get("pruning_required") == "1"
        pruning_method = request.form.get("pruning_method", "").strip()
        pruning_notes = request.form.get("pruning_notes", "").strip()

        if not plant_id or not name:
            return render_template(
                "automation_plant_add.html",
                error="Plant ID and name are required.",
                mode="add",
                form_data=request.form
            )

        if plant_exists(plant_id):
            return render_template(
                "automation_plant_add.html",
                error="Plant already exists. Use Edit or Add Variety.",
                mode="add",
                form_data=request.form
            )

        if not water_need:
            return render_template(
                "automation_plant_add.html",
                error="Water need is required.",
                mode="add",
                form_data=request.form
            )

        if not (sow_indoors_months or sow_outdoors_months or transplant_out_months):
            return render_template(
                "automation_plant_add.html",
                error="At least one sowing/transplant month field is required.",
                mode="add",
                form_data=request.form
            )

        if not harvest_months:
            return render_template(
                "automation_plant_add.html",
                error="Harvest months are required.",
                mode="add",
                form_data=request.form
            )

        try:
            spacing_in_row_cm = int(spacing_in_row_cm) if spacing_in_row_cm else None
            spacing_between_rows_cm = int(spacing_between_rows_cm) if spacing_between_rows_cm else None
            root_depth_min_cm = int(root_depth_min_cm) if root_depth_min_cm else None
            root_depth_max_cm = int(root_depth_max_cm) if root_depth_max_cm else None
            soil_ph_min = float(soil_ph_min) if soil_ph_min else None
            soil_ph_max = float(soil_ph_max) if soil_ph_max else None
            days_to_maturity_min = int(days_to_maturity_min) if days_to_maturity_min else None
            days_to_maturity_max = int(days_to_maturity_max) if days_to_maturity_max else None
        except ValueError:
            return render_template(
                "automation_plant_add.html",
                error="Numeric fields contain invalid values.",
                mode="add",
                form_data=request.form
            )

        irrigation_sensitivity = irrigation_sensitivity or "balanced"
        min_m, max_m, base_minutes = derive_watering_defaults(water_need, root_depth_max_cm)

        soil_json = {
            "drainage": soil_drainage or None,
            "pH_range": [soil_ph_min, soil_ph_max] if soil_ph_min is not None and soil_ph_max is not None else [],
            "notes": soil_notes or None,
        }

        calendar_json = {
            "base": {
                "sow_indoors": {"months": sow_indoors_months},
                "sow_outdoors": {"months": sow_outdoors_months},
                "transplant_out": {"months": transplant_out_months},
                "harvest": {"months": harvest_months},
            },
            "days_to_maturity_range": (
                [days_to_maturity_min, days_to_maturity_max]
                if days_to_maturity_min is not None and days_to_maturity_max is not None
                else []
            ),
        }

        nutrition_json = {
            "feeder": feeder or None,
            "emphasis": nutrition_emphasis or None,
            "notes": nutrition_notes or None,
        }

        care_json = {
            "support": {
                "needs_support": support_needed,
                "notes": support_notes or None,
            },
            "pruning": {
                "required": pruning_required,
                "method": pruning_method or None,
                "notes": pruning_notes or None,
            }
        }

        plant_json = {
            "schema_version": 1,
            "id": plant_id,
            "names": {
                "common": name,
                "scientific": scientific_name or None
            },
            "category": category or None,
            "family": family or None,
            "ui": {
                "icon_key": icon_key or None,
                "emoji": emoji or None,
                "photo_key": photo_key or None
            },
            "spacing_cm": {
                "in_row": spacing_in_row_cm,
                "between_rows": spacing_between_rows_cm
            },
            "roots": {
                "depth_cm_range": [root_depth_min_cm, root_depth_max_cm],
                "type": root_type or None
            },
            "soil": soil_json,
            "water_need": {
                "overall": water_need
            },
            "irrigation": {
                "sensitivity": irrigation_sensitivity,
                "mulch_helpful": mulch_helpful
            },
            "calendar": calendar_json,
            "nutrition": nutrition_json,
            "care": care_json,
            "companions": {
                "good": [],
                "avoid": []
            },
            "varieties": []
        }

        insert_rich_plant({
            "plant_id": plant_id,
            "name": name,
            "scientific_name": scientific_name or None,
            "category": category or None,
            "family": family or None,
            "icon_key": icon_key or None,
            "emoji": emoji or None,
            "photo_key": photo_key or None,
            "spacing_in_row_cm": spacing_in_row_cm,
            "spacing_between_rows_cm": spacing_between_rows_cm,
            "root_depth_min_cm": root_depth_min_cm,
            "root_depth_max_cm": root_depth_max_cm,
            "root_type": root_type or None,
            "water_need_overall": water_need,
            "irrigation_sensitivity": irrigation_sensitivity,
            "mulch_helpful": mulch_helpful,
            "min_moisture": min_m,
            "max_moisture": max_m,
            "base_minutes": base_minutes,
            "soil_json": soil_json,
            "calendar_json": calendar_json,
            "nutrition_json": nutrition_json,
            "care_json": care_json,
            "plant_json": plant_json,
            "schema_version": 1,
        })

        return redirect(url_for("plant.automation_plants"))

    return render_template("automation_plant_add.html", mode="add", form_data={})


@plant_bp.route("/automation/plants/<plant_id>/edit", methods=["GET", "POST"])
def automation_plants_edit(plant_id):
    plant = get_plant_by_id(plant_id)
    if not plant:
        return "Plant not found.", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        scientific_name = request.form.get("scientific_name", "").strip()
        category = request.form.get("category", "").strip()
        family = request.form.get("family", "").strip()

        emoji = request.form.get("emoji", "").strip()
        icon_key = request.form.get("icon_key", "").strip()
        photo_key = request.form.get("photo_key", "").strip()

        spacing_in_row_cm = request.form.get("spacing_in_row_cm", "").strip()
        spacing_between_rows_cm = request.form.get("spacing_between_rows_cm", "").strip()

        root_depth_min_cm = request.form.get("root_depth_min_cm", "").strip()
        root_depth_max_cm = request.form.get("root_depth_max_cm", "").strip()
        root_type = request.form.get("root_type", "").strip()

        water_need = request.form.get("water_need", "").strip().lower()
        irrigation_sensitivity = request.form.get("irrigation_sensitivity", "").strip().lower()
        mulch_helpful = request.form.get("mulch_helpful") == "1"

        soil_drainage = request.form.get("soil_drainage", "").strip()
        soil_ph_min = request.form.get("soil_ph_min", "").strip()
        soil_ph_max = request.form.get("soil_ph_max", "").strip()
        soil_notes = request.form.get("soil_notes", "").strip()

        feeder = request.form.get("feeder", "").strip()
        nutrition_emphasis = request.form.get("nutrition_emphasis", "").strip()
        nutrition_notes = request.form.get("nutrition_notes", "").strip()

        sow_indoors_months = parse_months(request.form.get("sow_indoors_months", ""))
        sow_outdoors_months = parse_months(request.form.get("sow_outdoors_months", ""))
        transplant_out_months = parse_months(request.form.get("transplant_out_months", ""))
        harvest_months = parse_months(request.form.get("harvest_months", ""))

        days_to_maturity_min = request.form.get("days_to_maturity_min", "").strip()
        days_to_maturity_max = request.form.get("days_to_maturity_max", "").strip()

        support_needed = request.form.get("support_needed") == "1"
        support_notes = request.form.get("support_notes", "").strip()

        pruning_required = request.form.get("pruning_required") == "1"
        pruning_method = request.form.get("pruning_method", "").strip()
        pruning_notes = request.form.get("pruning_notes", "").strip()

        if not name:
            return render_template(
                "automation_plant_add.html",
                error="Name is required.",
                mode="edit",
                form_data=request.form,
                plant_id_locked=plant_id
            )

        if not water_need:
            return render_template(
                "automation_plant_add.html",
                error="Water need is required.",
                mode="edit",
                form_data=request.form,
                plant_id_locked=plant_id
            )

        if not (sow_indoors_months or sow_outdoors_months or transplant_out_months):
            return render_template(
                "automation_plant_add.html",
                error="At least one sowing/transplant month field is required.",
                mode="edit",
                form_data=request.form,
                plant_id_locked=plant_id
            )

        if not harvest_months:
            return render_template(
                "automation_plant_add.html",
                error="Harvest months are required.",
                mode="edit",
                form_data=request.form,
                plant_id_locked=plant_id
            )

        try:
            spacing_in_row_cm = int(spacing_in_row_cm) if spacing_in_row_cm else None
            spacing_between_rows_cm = int(spacing_between_rows_cm) if spacing_between_rows_cm else None
            root_depth_min_cm = int(root_depth_min_cm) if root_depth_min_cm else None
            root_depth_max_cm = int(root_depth_max_cm) if root_depth_max_cm else None
            soil_ph_min = float(soil_ph_min) if soil_ph_min else None
            soil_ph_max = float(soil_ph_max) if soil_ph_max else None
            days_to_maturity_min = int(days_to_maturity_min) if days_to_maturity_min else None
            days_to_maturity_max = int(days_to_maturity_max) if days_to_maturity_max else None
        except ValueError:
            return render_template(
                "automation_plant_add.html",
                error="Numeric fields contain invalid values.",
                mode="edit",
                form_data=request.form,
                plant_id_locked=plant_id
            )

        irrigation_sensitivity = irrigation_sensitivity or "balanced"
        min_m, max_m, base_minutes = derive_watering_defaults(water_need, root_depth_max_cm)

        soil_json = {
            "drainage": soil_drainage or None,
            "pH_range": [soil_ph_min, soil_ph_max] if soil_ph_min is not None and soil_ph_max is not None else [],
            "notes": soil_notes or None,
        }

        calendar_json = {
            "base": {
                "sow_indoors": {"months": sow_indoors_months},
                "sow_outdoors": {"months": sow_outdoors_months},
                "transplant_out": {"months": transplant_out_months},
                "harvest": {"months": harvest_months},
            },
            "days_to_maturity_range": (
                [days_to_maturity_min, days_to_maturity_max]
                if days_to_maturity_min is not None and days_to_maturity_max is not None
                else []
            ),
        }

        nutrition_json = {
            "feeder": feeder or None,
            "emphasis": nutrition_emphasis or None,
            "notes": nutrition_notes or None,
        }

        care_json = {
            "support": {
                "needs_support": support_needed,
                "notes": support_notes or None,
            },
            "pruning": {
                "required": pruning_required,
                "method": pruning_method or None,
                "notes": pruning_notes or None,
            }
        }

        plant_json = {
            "schema_version": 1,
            "id": plant_id,
            "names": {
                "common": name,
                "scientific": scientific_name or None
            },
            "category": category or None,
            "family": family or None,
            "ui": {
                "icon_key": icon_key or None,
                "emoji": emoji or None,
                "photo_key": photo_key or None
            },
            "spacing_cm": {
                "in_row": spacing_in_row_cm,
                "between_rows": spacing_between_rows_cm
            },
            "roots": {
                "depth_cm_range": [root_depth_min_cm, root_depth_max_cm],
                "type": root_type or None
            },
            "soil": soil_json,
            "water_need": {
                "overall": water_need
            },
            "irrigation": {
                "sensitivity": irrigation_sensitivity,
                "mulch_helpful": mulch_helpful
            },
            "calendar": calendar_json,
            "nutrition": nutrition_json,
            "care": care_json,
            "companions": {
                "good": [],
                "avoid": []
            },
            "varieties": []
        }

        update_rich_plant(plant_id, {
            "name": name,
            "scientific_name": scientific_name or None,
            "category": category or None,
            "family": family or None,
            "icon_key": icon_key or None,
            "emoji": emoji or None,
            "photo_key": photo_key or None,
            "spacing_in_row_cm": spacing_in_row_cm,
            "spacing_between_rows_cm": spacing_between_rows_cm,
            "root_depth_min_cm": root_depth_min_cm,
            "root_depth_max_cm": root_depth_max_cm,
            "root_type": root_type or None,
            "water_need_overall": water_need,
            "irrigation_sensitivity": irrigation_sensitivity,
            "mulch_helpful": mulch_helpful,
            "min_moisture": min_m,
            "max_moisture": max_m,
            "base_minutes": base_minutes,
            "soil_json": soil_json,
            "calendar_json": calendar_json,
            "nutrition_json": nutrition_json,
            "care_json": care_json,
            "plant_json": plant_json,
            "schema_version": 1,
        })

        return redirect(url_for("plant.automation_plant_detail", plant_id=plant_id))

    return render_template(
        "automation_plant_add.html",
        mode="edit",
        form_data=plant_to_form_data(plant),
        plant_id_locked=plant_id
    )

