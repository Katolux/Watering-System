from flask import Blueprint, request, render_template, redirect, url_for
import json
from repositories import (
    get_all_plants_catalog,
    get_plant_by_id,
    plant_exists,
    insert_rich_plant,
    update_rich_plant,
    delete_plant,
    variety_exists,
    get_plant_varieties,
    delete_variety,
    get_plant_companions,
    insert_rich_variety,
)


plant_bp = Blueprint("plant", __name__)

def parse_months(raw_value):
    if not raw_value:
        return []

    parts = [p.strip() for p in raw_value.split(",")]
    months = []

    for p in parts:
        if not p:
            continue
        try:
            m = int(p)
        except ValueError:
            continue

        if 1 <= m <= 12:
            months.append(m)

    return months

def derive_watering_defaults(water_need, root_depth_max):
    defaults = {
        "low":    {"min_moisture": 35, "max_moisture": 55, "base_minutes": 25},
        "medium": {"min_moisture": 50, "max_moisture": 70, "base_minutes": 35},
        "high":   {"min_moisture": 60, "max_moisture": 80, "base_minutes": 45},
    }

    chosen = defaults.get(water_need, defaults["medium"])

    min_m = chosen["min_moisture"]
    max_m = chosen["max_moisture"]
    base_minutes = chosen["base_minutes"]

    if root_depth_max is not None:
        if root_depth_max < 30:
            min_m += 5
            max_m += 5
            base_minutes -= 5
        elif root_depth_max > 60:
            min_m -= 5
            max_m -= 5
            base_minutes += 10

    min_m = max(0, min(100, min_m))
    max_m = max(0, min(100, max_m))
    base_minutes = max(5, base_minutes)

    return min_m, max_m, base_minutes

def plant_to_form_data(plant):
    soil = json.loads(plant[19]) if plant[19] else {}
    calendar = json.loads(plant[20]) if plant[20] else {}
    nutrition = json.loads(plant[21]) if plant[21] else {}
    care = json.loads(plant[22]) if plant[22] else {}

    base = calendar.get("base", {})
    soil_ph = soil.get("pH_range", [])
    support = care.get("support", {})
    pruning = care.get("pruning", {})

    return {
        "plant_id": plant[0] or "",
        "name": plant[1] or "",
        "scientific_name": plant[2] or "",
        "category": plant[3] or "",
        "family": plant[4] or "",
        "icon_key": plant[5] or "",
        "emoji": plant[6] or "",
        "photo_key": plant[7] or "",
        "spacing_in_row_cm": plant[8] or "",
        "spacing_between_rows_cm": plant[9] or "",
        "root_depth_min_cm": plant[10] or "",
        "root_depth_max_cm": plant[11] or "",
        "root_type": plant[12] or "",
        "water_need": plant[13] or "medium",
        "irrigation_sensitivity": plant[14] or "balanced",
        "mulch_helpful": bool(plant[15]),

        "soil_drainage": soil.get("drainage") or "",
        "soil_ph_min": soil_ph[0] if len(soil_ph) > 0 and soil_ph[0] is not None else "",
        "soil_ph_max": soil_ph[1] if len(soil_ph) > 1 and soil_ph[1] is not None else "",
        "soil_notes": soil.get("notes") or "",

        "feeder": nutrition.get("feeder") or "",
        "nutrition_emphasis": nutrition.get("emphasis") or "",
        "nutrition_notes": nutrition.get("notes") or "",

        "sow_indoors_months": ",".join(str(m) for m in base.get("sow_indoors", {}).get("months", [])),
        "sow_outdoors_months": ",".join(str(m) for m in base.get("sow_outdoors", {}).get("months", [])),
        "transplant_out_months": ",".join(str(m) for m in base.get("transplant_out", {}).get("months", [])),
        "harvest_months": ",".join(str(m) for m in base.get("harvest", {}).get("months", [])),

        "days_to_maturity_min": (
            calendar.get("days_to_maturity_range", [None, None])[0]
            if calendar.get("days_to_maturity_range")
            else ""
        ),
        "days_to_maturity_max": (
            calendar.get("days_to_maturity_range", [None, None])[1]
            if calendar.get("days_to_maturity_range")
            else ""
        ),

        "support_needed": bool(support.get("needs_support")),
        "support_notes": support.get("notes") or "",

        "pruning_required": bool(pruning.get("required")),
        "pruning_method": pruning.get("method") or "",
        "pruning_notes": pruning.get("notes") or "",
    }


@plant_bp.route("/automation/plants")
def automation_plants():
    rows = get_all_plants_catalog()

    plants = []
    for row in rows:
        plant_id, name, category, family, emoji, water_need, calendar_json = row

        calendar = json.loads(calendar_json) if calendar_json else {}
        base = calendar.get("base", {})

        sow_indoors = base.get("sow_indoors", {}).get("months", [])
        sow_outdoors = base.get("sow_outdoors", {}).get("months", [])
        transplant_out = base.get("transplant_out", {}).get("months", [])
        harvest = base.get("harvest", {}).get("months", [])

        plants.append({
            "plant_id": plant_id,
            "name": name,
            "category": category,
            "family": family,
            "emoji": emoji,
            "water_need": water_need,
            "sow_indoors": sow_indoors,
            "sow_outdoors": sow_outdoors,
            "transplant_out": transplant_out,
            "harvest": harvest,
        })

    return render_template("automation_plants.html", plants=plants)

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


@plant_bp.route("/automation/plants/<plant_id>")
def automation_plant_detail(plant_id):
    plant = get_plant_by_id(plant_id)
    if not plant:
        return "Plant not found.", 404

    varieties = get_plant_varieties(plant_id)
    companions = get_plant_companions(plant_id)

    soil = json.loads(plant[19]) if plant[19] else {}
    calendar = json.loads(plant[20]) if plant[20] else {}
    nutrition = json.loads(plant[21]) if plant[21] else {}
    care = json.loads(plant[22]) if plant[22] else {}

    return render_template(
        "automation_plant_detail.html",
        plant=plant,
        varieties=varieties,
        companions=companions,
        soil=soil,
        calendar=calendar,
        nutrition=nutrition,
        care=care
    )

@plant_bp.route("/automation/plants/edit-select", methods=["POST"])
def automation_plants_edit_select():
    plant_id = request.form.get("plant_id", "").strip().lower()

    if not plant_id or not plant_exists(plant_id):
        return redirect(url_for("plant.automation_plants"))

    return redirect(url_for("plant.automation_plants_edit", plant_id=plant_id))

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

@plant_bp.route("/automation/plants/delete-select", methods=["POST"])
def automation_plants_delete_select():
    plant_id = request.form.get("plant_id", "").strip().lower()
    plant = get_plant_by_id(plant_id)

    if not plant:
        return redirect(url_for("plant.automation_plants"))

    return render_template(
        "automation_plant_confirm_delete.html",
        plant=plant
    )


@plant_bp.route("/automation/plants/<plant_id>/delete-confirm", methods=["POST"])
def automation_plant_delete_confirm(plant_id):
    if not plant_exists(plant_id):
        return "Plant not found.", 404

    delete_plant(plant_id)
    return redirect(url_for("plant.automation_plants"))

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
