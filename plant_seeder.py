import json
from pathlib import Path
from repositories import add_plant


def slugify(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )


def seed_from_file(json_path: str | Path) -> None:
    json_path = Path(json_path)

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    base_id = data["plant_id"]
    common_name = data["common_name"]

    defaults = data["defaults"]["watering"]
    min_m = defaults["moisture_targets"]["min_moisture"]
    max_m = defaults["moisture_targets"]["max_moisture"]
    base_minutes = defaults["base_minutes"]

    varieties = data.get("varieties", [])
    if varieties:
        for v in varieties:
            # varieties can be either a string or an object
            if isinstance(v, str):
                v_name = v
                overrides = {}
            elif isinstance(v, dict):
                v_name = v.get("name")
                overrides = v.get("watering_overrides", {}) or {}
            else:
                continue

            if not v_name:
                continue

            vid = f"{base_id}:{slugify(v_name)}"
            name = f"{common_name} - {v_name}"

            ov_targets = (overrides.get("moisture_targets") or {})
            v_min = ov_targets.get("min_moisture", min_m)
            v_max = ov_targets.get("max_moisture", max_m)
            v_base = overrides.get("base_minutes", base_minutes)

            add_plant(vid, name, v_min, v_max, v_base)

    else:
        # No varieties -> seed base plant
        add_plant(base_id, common_name, min_m, max_m, base_minutes)


def seed_directory(dir_path: str | Path = "plants") -> None:
    dir_path = Path(dir_path)

    if not dir_path.exists():
        raise FileNotFoundError(f"Plants directory not found: {dir_path}")

    for file in sorted(dir_path.glob("*.json")):
        seed_from_file(file)
