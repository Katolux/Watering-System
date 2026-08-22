from flask import request, render_template, redirect, url_for
from gardenhub.repositories.plants_repo import (
    get_encyclopedia_catalog,
    get_plant_by_id,
    plant_exists,
    delete_plant,
    get_encyclopedia_varieties,
    get_encyclopedia_companions,
)
from gardenhub.routes.plants import plant_bp
from gardenhub.services.plant_encyclopedia import (
    PLANT_DETAIL_TABS,
    PLANT_DETAIL_TAB_KEYS,
    build_catalog_item,
    build_plant_detail,
)


@plant_bp.route("/automation/plants")
def automation_plants():
    plants = [build_catalog_item(row) for row in get_encyclopedia_catalog()]

    return render_template("automation_plants.html", plants=plants)


@plant_bp.route("/automation/plants/<plant_id>")
def automation_plant_detail(plant_id):
    plant = get_plant_by_id(plant_id)
    if not plant:
        return "Plant not found.", 404

    encyclopedia_plant = build_plant_detail(
        plant,
        get_encyclopedia_varieties(plant_id),
        get_encyclopedia_companions(plant_id),
    )

    active_tab = request.args.get("tab", "overview")
    if active_tab not in PLANT_DETAIL_TAB_KEYS:
        active_tab = "overview"

    return render_template(
        "automation_plant_detail.html",
        plant=encyclopedia_plant,
        tabs=PLANT_DETAIL_TABS,
        active_tab=active_tab,
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
