from flask import request, render_template, redirect, url_for
import json
from gardenhub.repositories.plants_repo import (
    get_all_plants_catalog,
    get_plant_by_id,
    plant_exists,
    delete_plant,
    get_plant_varieties,
    get_plant_companions,
)
from gardenhub.routes.plants import plant_bp


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
