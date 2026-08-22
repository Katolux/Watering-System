"""Presentation helpers for the user-facing plant Encyclopedia."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = PROJECT_ROOT / "static"
ASSET_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png")
MONTH_NAMES = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

PLANT_DETAIL_TABS = (
    ("overview", "Overview", "sprout"),
    ("growing-guide", "Growing guide", "book"),
    ("calendar", "Calendar", "calendar"),
    ("companions", "Companions", "users"),
    ("pests-diseases", "Pests & diseases", "alert"),
    ("soil-fertilisation", "Soil & fertilisation", "flask"),
    ("harvest-storage", "Harvest & storage", "container"),
)
PLANT_DETAIL_TAB_KEYS = {tab[0] for tab in PLANT_DETAIL_TABS}

BEST_USE_PRESENTATION = {
    "fresh_eating": ("Fresh eating", "sprout"),
    "salads": ("Salads", "sprout"),
    "sauces": ("Sauces", "container"),
    "roasting": ("Roasting", "sun"),
    "cooking": ("Cooking", "flask"),
    "preserving": ("Preserving", "container"),
}


def _json_object(value):
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _humanize(value):
    if value is None or value == "":
        return None
    return str(value).replace("_", " ").strip().title()


def _range_label(values, unit=""):
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        return None
    if values[0] is None or values[1] is None:
        return None
    suffix = f" {unit}" if unit else ""
    return f"{values[0]}–{values[1]}{suffix}"


def _month_numbers(value):
    if not isinstance(value, list):
        return []
    return [month for month in value if isinstance(month, int) and 1 <= month <= 12]


def _month_label(months):
    values = _month_numbers(months)
    if not values:
        return None
    if len(values) == 1:
        return MONTH_NAMES[values[0]]
    consecutive = all(right == left + 1 for left, right in zip(values, values[1:]))
    if consecutive:
        return f"{MONTH_NAMES[values[0]]} – {MONTH_NAMES[values[-1]]}"
    return ", ".join(MONTH_NAMES[month] for month in values)


def _resolve_asset(key, folders):
    if not key:
        return None
    safe_key = Path(str(key)).stem
    for folder in folders:
        for extension in ASSET_EXTENSIONS:
            relative = Path("images") / folder / f"{safe_key}{extension}"
            if (STATIC_ROOT / relative).is_file():
                return relative.as_posix()
    return None


def _resolve_botanical_asset(key, plant_id):
    asset = _resolve_asset(key, ("botanical", "plants"))
    if asset or plant_id != "tomato":
        return asset
    return _resolve_asset(key, ("botanical/planner",))


def _frost_label(values):
    if not isinstance(values, list) or len(values) != 2:
        return None
    start, end = values
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    if end <= 0:
        return f"{abs(start)}–{abs(end)} weeks before last frost"
    if start >= 0:
        return f"{start}–{end} weeks after last frost"
    return f"{abs(start)} weeks before to {end} weeks after last frost"


def _calendar_event(key, title, event):
    event = event if isinstance(event, dict) else {}
    months = _month_numbers(event.get("months"))
    return {
        "key": key,
        "title": title,
        "months": months,
        "month_label": _month_label(months),
        "recommended": event.get("recommended") is not False,
        "reason": event.get("reason"),
        "notes": event.get("notes"),
        "frost_label": _frost_label(event.get("weeks_relative_to_last_frost")),
    }


def _best_uses(values):
    items = []
    for value in values if isinstance(values, list) else []:
        label, icon = BEST_USE_PRESENTATION.get(value, (_humanize(value), "check"))
        items.append({"key": value, "label": label, "icon": icon})
    return items


def _level_guidance(level, notes=None):
    return {"level": _humanize(level), "notes": notes}


def build_catalog_item(row):
    (
        plant_id,
        name,
        scientific_name,
        category,
        family,
        icon_key,
        photo_key,
        spacing,
        water_need,
        calendar_json,
        plant_json,
    ) = row
    document = _json_object(plant_json)
    ui = document.get("ui", {})
    calendar = document.get("calendar") or _json_object(calendar_json)
    maturity = calendar.get("days_to_maturity_range")
    highlight_one = _range_label(maturity, "days")
    if highlight_one:
        highlight_one = f"Harvest in {highlight_one}"
    else:
        harvest_label = _month_label(calendar.get("base", {}).get("harvest", {}).get("months"))
        highlight_one = f"Harvest {harvest_label}" if harvest_label else None
    spacing_value = document.get("spacing_cm", {}).get("in_row", spacing)
    highlight_two = f"{spacing_value} cm spacing" if spacing_value is not None else None
    overall_water = document.get("water_need", {}).get("overall", water_need)
    if not highlight_two and overall_water:
        highlight_two = f"{_humanize(overall_water)} water need"
    photo_asset = _resolve_asset(ui.get("photo_key", photo_key), ("plants",))
    botanical_asset = _resolve_botanical_asset(ui.get("icon_key", icon_key), plant_id)
    return {
        "plant_id": plant_id,
        "name": name,
        "scientific_name": scientific_name,
        "category": _humanize(category),
        "family": family,
        "image": photo_asset,
        "botanical_image": botanical_asset,
        "prefer_botanical": plant_id == "tomato" and bool(botanical_asset),
        "highlights": [item for item in (highlight_one, highlight_two) if item][:2],
        "search_text": " ".join(value for value in (name, scientific_name, category, family) if value).lower(),
    }


def build_variety(row):
    _variety_id, name, notes, overrides_json, resolved_json = row
    resolved = _json_object(resolved_json)
    overrides = _json_object(overrides_json)
    maturity = (resolved.get("calendar") or overrides.get("calendar", {})).get("days_to_maturity_range")
    return {"name": name, "notes": notes, "maturity": _range_label(maturity, "days")}


def build_companion(row):
    plant_id, name, scientific_name, relation, reason, confidence, mechanism = row
    return {
        "plant_id": plant_id,
        "name": name,
        "scientific_name": scientific_name,
        "relation": relation,
        "reason": reason,
        "confidence": _humanize(confidence),
        "mechanism": _humanize(mechanism),
    }


def build_plant_detail(plant, variety_rows, companion_rows):
    document = _json_object(plant[23])
    ui = document.get("ui", {})
    overview = document.get("overview", {})
    spacing = document.get("spacing_cm", {})
    support = document.get("support", {})
    roots = document.get("roots", {})
    light = document.get("light", {})
    soil = document.get("soil") or _json_object(plant[19])
    water = document.get("water_need", {})
    irrigation = document.get("irrigation", {})
    calendar = document.get("calendar") or _json_object(plant[20])
    nutrition = document.get("nutrition") or _json_object(plant[21])
    nutrition_emphasis = nutrition.get("emphasis", {})
    if not isinstance(nutrition_emphasis, dict):
        nutrition_emphasis = {}
    care = document.get("care") or _json_object(plant[22])
    harvest_storage = document.get("harvest_storage", {})
    seed_saving = document.get("seed_saving", {})
    base_calendar = calendar.get("base", {})

    plant_id = plant[0]
    icon_key = ui.get("icon_key", plant[5])
    photo_key = ui.get("photo_key", plant[7])
    image = _resolve_asset(photo_key, ("plants",))
    botanical_image = _resolve_botanical_asset(icon_key, plant_id)

    height_label = _range_label(support.get("height_cm_range"), "cm")
    spread_label = _range_label(support.get("spread_cm_range"), "cm")
    in_row = spacing.get("in_row", plant[8])
    between_rows = spacing.get("between_rows", plant[9])
    maturity_label = _range_label(calendar.get("days_to_maturity_range"), "days")

    tags = [
        _humanize(overview.get("plant_type")),
        _humanize(light.get("requirement")),
        f"{_humanize(water.get('overall'))} Water" if water.get("overall") else None,
        "Support Required" if support.get("needs_trellis") else None,
        f"{_humanize(nutrition.get('feeder'))} Feeder" if nutrition.get("feeder") else None,
    ]

    water_stages = []
    for stage, guidance in water.get("stage_profile", {}).items():
        guidance = guidance if isinstance(guidance, dict) else {"level": guidance}
        water_stages.append({"stage": _humanize(stage), **_level_guidance(guidance.get("level"), guidance.get("notes"))})

    companions = [build_companion(row) for row in companion_rows]
    preservation = harvest_storage.get("preservation", {})
    storage = harvest_storage.get("storage", {})
    seed_possible = seed_saving.get("possible")

    return {
        "plant_id": plant_id,
        "name": plant[1],
        "scientific_name": plant[2],
        "category": _humanize(plant[3]),
        "family": plant[4],
        "image": image,
        "botanical_image": botanical_image,
        "growth_habit_visual": _resolve_asset(ui.get("growth_habit_image"), ("encyclopedia",)),
        "mature_size_visual": _resolve_asset(ui.get("mature_size_image"), ("encyclopedia",)),
        "asset_version": 2,
        "tags": [tag for tag in tags if tag],
        "summary": overview.get("summary"),
        "quick_stats": [
            {"label": "Days to harvest", "value": maturity_label, "detail": None, "icon": "calendar"},
            {"label": "Mature size", "value": f"{height_label} tall" if height_label else None, "detail": f"{spread_label} spread" if spread_label else None, "icon": "sprout"},
            {"label": "Spacing", "value": f"{in_row} cm in-row" if in_row is not None else None, "detail": f"{between_rows} cm between rows" if between_rows is not None else None, "icon": "layout"},
            {"label": "Sun", "value": _humanize(light.get("requirement")), "detail": f"{light.get('minimum_hours')}–{light.get('preferred_hours')} hours daily" if light.get("minimum_hours") is not None and light.get("preferred_hours") is not None else None, "icon": "sun"},
            {"label": "Water", "value": _humanize(water.get("overall")), "detail": _humanize(irrigation.get("sensitivity")), "icon": "droplet"},
        ],
        "quick_facts": [
            ("Type", _humanize(document.get("category", plant[3]))),
            ("Family", document.get("family", plant[4])),
            ("Plant type", _humanize(overview.get("plant_type"))),
            ("Growth habit", _humanize(overview.get("growth_habit"))),
            ("Root system", roots.get("label") or _humanize(roots.get("type"))),
            ("Lifecycle", _humanize(overview.get("lifecycle"))),
            ("Hardiness", _humanize(overview.get("hardiness"))),
            ("Containers", "Suitable" if overview.get("container_suitable") is True else "Not recommended" if overview.get("container_suitable") is False else None),
            ("Seed saving", f"Yes · {_humanize(seed_saving.get('difficulty'))}" if seed_possible is True else "No" if seed_possible is False else None),
        ],
        "growth_habit": {
            "label": _humanize(overview.get("growth_habit")),
            "support_needed": support.get("needs_trellis"),
            "support_methods": [_humanize(value) for value in support.get("methods", [])],
            "support_notes": support.get("notes"),
            "pruning_notes": care.get("pruning", {}).get("notes"),
        },
        "mature_size": {"height": height_label, "spread": spread_label},
        "best_uses": _best_uses(overview.get("best_uses", [])),
        "interesting_facts": overview.get("interesting_facts", []),
        "growing": {
            "water_summary": water.get("summary"),
            "water_stages": water_stages,
            "irrigation": {
                "sensitivity": _humanize(irrigation.get("sensitivity")),
                "preferred_method": _humanize(irrigation.get("preferred_method")),
                "foliage_notes": irrigation.get("foliage_notes"),
                "rain_notes": overview.get("rain_notes"),
            },
            "support": {
                "required": support.get("needs_trellis"),
                "methods": [_humanize(value) for value in support.get("methods", [])],
                "notes": support.get("notes"),
            },
            "pruning": {
                "recommended": care.get("pruning", {}).get("recommended"),
                "required": care.get("pruning", {}).get("required"),
                "method": _humanize(care.get("pruning", {}).get("method")),
                "notes": care.get("pruning", {}).get("notes"),
            },
            "pollination": {
                "type": _humanize(care.get("pollination", {}).get("type")),
                "notes": care.get("pollination", {}).get("aid_notes"),
            },
            "mulch": care.get("mulch", {}),
            "containers": care.get("containers", {}),
        },
        "calendar": {
            "events": [
                _calendar_event("sow-indoors", "Sow indoors", base_calendar.get("sow_indoors")),
                _calendar_event("sow-outdoors", "Sow outdoors", base_calendar.get("sow_outdoors")),
                _calendar_event("transplant", "Transplant", base_calendar.get("transplant_out")),
                _calendar_event("harvest", "Harvest", base_calendar.get("harvest")),
            ],
            "germination_temperature": _range_label(calendar.get("germination", {}).get("temperature_c_range"), "°C"),
            "frost_tolerance": _humanize(calendar.get("frost_tolerance")),
        },
        "good_companions": [item for item in companions if item["relation"] == "good"],
        "avoid_companions": [item for item in companions if item["relation"] != "good"],
        "pests_diseases": document.get("pests_diseases", {}).get("common", []),
        "soil": {
            "textures": [_humanize(value) for value in soil.get("preferred_textures", [])],
            "drainage": _humanize(soil.get("drainage")),
            "ph": _range_label(soil.get("pH_range")),
            "organic_matter": _humanize(soil.get("organic_matter")),
            "notes": soil.get("notes"),
        },
        "nutrition": {
            "feeder": _humanize(nutrition.get("feeder")),
            "schedule": _humanize(nutrition.get("schedule_hint")),
            "early_growth": _humanize(nutrition_emphasis.get("early_growth")),
            "flowering_fruiting": _humanize(nutrition_emphasis.get("flowering_fruiting")),
            "notes": nutrition.get("notes"),
        },
        "harvest_storage": {
            "harvest_guidance": harvest_storage.get("harvest_guidance"),
            "quality_notes": harvest_storage.get("quality_notes"),
            "storage": [
                {"key": key, "label": _humanize(key), "recommended": value.get("recommended"), "notes": value.get("notes")}
                for key, value in storage.items() if isinstance(value, dict)
            ],
            "preservation_suitable": preservation.get("suitable"),
            "preservation_methods": [_humanize(value) for value in preservation.get("methods", [])],
            "seed_saving": {
                "possible": seed_possible,
                "difficulty": _humanize(seed_saving.get("difficulty")),
                "method": _humanize(seed_saving.get("method")),
                "notes": seed_saving.get("notes"),
                "pollination_notes": seed_saving.get("pollination_notes"),
                "hybrid_warning": seed_saving.get("hybrid_warning"),
            },
        },
        "varieties": [build_variety(row) for row in variety_rows],
    }
