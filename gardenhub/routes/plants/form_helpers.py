import json


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
