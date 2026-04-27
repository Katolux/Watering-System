import json
from pathlib import Path
from copy import deepcopy

from db import get_conn


WATER_NEED_DEFAULTS = {
    "low":    {"min_moisture": 35, "max_moisture": 55, "base_minutes": 25},
    "medium": {"min_moisture": 50, "max_moisture": 70, "base_minutes": 35},
    "high":   {"min_moisture": 60, "max_moisture": 80, "base_minutes": 45},
}


REQUIRED_KEYS = [
    "schema_version",
    "id",
    "names",
    "category",
    "family",
    "ui",
    "spacing_cm",
    "roots",
    "soil",
    "water_need",
    "irrigation",
    "calendar",
    "nutrition",
    "care",
    "companions",
    "varieties",
]


def deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def derive_watering_defaults(plant_data: dict) -> tuple[int, int, int]:
    water_need = (
        plant_data.get("water_need", {}).get("overall", "medium")
    ).lower()

    defaults = WATER_NEED_DEFAULTS.get(
        water_need,
        WATER_NEED_DEFAULTS["medium"]
    )

    min_m = defaults["min_moisture"]
    max_m = defaults["max_moisture"]
    base_minutes = defaults["base_minutes"]

    depth_range = plant_data.get("roots", {}).get("depth_cm_range", [])
    root_depth_max = None
    if isinstance(depth_range, list) and len(depth_range) == 2:
        root_depth_max = depth_range[1]

    if isinstance(root_depth_max, int):
        if root_depth_max < 30:
            min_m += 5
            max_m += 5
            base_minutes -= 5
        elif root_depth_max > 60:
            min_m -= 5
            max_m -= 5
            base_minutes += 10

    min_m = clamp(min_m, 0, 100)
    max_m = clamp(max_m, 0, 100)
    base_minutes = max(5, base_minutes)

    if min_m > max_m:
        min_m, max_m = max_m, min_m

    return min_m, max_m, base_minutes


def validate_plant_json(data: dict, source_name: str = "") -> None:
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{source_name}: missing required keys: {missing}")

    if not isinstance(data["names"], dict):
        raise ValueError(f"{source_name}: names must be an object")

    if "common" not in data["names"]:
        raise ValueError(f"{source_name}: names.common is required")

    if not isinstance(data["varieties"], list):
        raise ValueError(f"{source_name}: varieties must be a list")

    if "overall" not in data.get("water_need", {}):
        raise ValueError(f"{source_name}: water_need.overall is required")

    if "depth_cm_range" not in data.get("roots", {}):
        raise ValueError(f"{source_name}: roots.depth_cm_range is required")

    if "in_row" not in data.get("spacing_cm", {}):
        raise ValueError(f"{source_name}: spacing_cm.in_row is required")

    if "between_rows" not in data.get("spacing_cm", {}):
        raise ValueError(f"{source_name}: spacing_cm.between_rows is required")


def insert_plant(cur, plant_data: dict) -> None:
    min_m, max_m, base_minutes = derive_watering_defaults(plant_data)

    names = plant_data.get("names", {})
    ui = plant_data.get("ui", {})
    spacing = plant_data.get("spacing_cm", {})
    roots = plant_data.get("roots", {})
    irrigation = plant_data.get("irrigation", {})

    depth_range = roots.get("depth_cm_range", [None, None])
    if not isinstance(depth_range, list) or len(depth_range) != 2:
        depth_range = [None, None]

    cur.execute(
        """
        INSERT OR REPLACE INTO plants (
            plant_id,
            name,
            scientific_name,
            category,
            family,
            icon_key,
            emoji,
            photo_key,
            spacing_in_row_cm,
            spacing_between_rows_cm,
            root_depth_min_cm,
            root_depth_max_cm,
            root_type,
            water_need_overall,
            irrigation_sensitivity,
            mulch_helpful,
            min_moisture,
            max_moisture,
            base_minutes,
            soil_json,
            calendar_json,
            nutrition_json,
            care_json,
            plant_json,
            schema_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plant_data["id"],
            names.get("common"),
            names.get("scientific"),
            plant_data.get("category"),
            plant_data.get("family"),
            ui.get("icon_key"),
            ui.get("emoji"),
            ui.get("photo_key"),
            spacing.get("in_row"),
            spacing.get("between_rows"),
            depth_range[0],
            depth_range[1],
            roots.get("type"),
            plant_data.get("water_need", {}).get("overall"),
            irrigation.get("sensitivity"),
            1 if irrigation.get("mulch_helpful") else 0,
            min_m,
            max_m,
            base_minutes,
            json.dumps(plant_data.get("soil", {}), ensure_ascii=False),
            json.dumps(plant_data.get("calendar", {}), ensure_ascii=False),
            json.dumps(plant_data.get("nutrition", {}), ensure_ascii=False),
            json.dumps(plant_data.get("care", {}), ensure_ascii=False),
            json.dumps(plant_data, ensure_ascii=False),
            plant_data.get("schema_version", 1),
        )
    )


def insert_companions(cur, plant_data: dict) -> None:
    plant_id = plant_data["id"]
    companions = plant_data.get("companions", {})

    cur.execute(
        "DELETE FROM plant_companions WHERE plant_id = ?",
        (plant_id,)
    )

    for relation in ("good", "avoid"):
        for entry in companions.get(relation, []):
            other_plant_id = entry.get("plant_id")
            if not other_plant_id:
                continue

            cur.execute(
                "SELECT 1 FROM plants WHERE plant_id = ?",
                (other_plant_id,)
            )
            exists = cur.fetchone()

            if not exists:
                print(
                    f"WARNING: skipping companion link "
                    f"{plant_id} -> {other_plant_id} "
                    f"(target plant not found)"
                )
                continue

            cur.execute(
                """
                INSERT OR REPLACE INTO plant_companions (
                    plant_id,
                    other_plant_id,
                    relation,
                    reason,
                    confidence,
                    mechanism
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    plant_id,
                    other_plant_id,
                    relation,
                    entry.get("reason"),
                    entry.get("confidence"),
                    entry.get("mechanism"),
                )
            )

def insert_varieties(cur, plant_data: dict) -> None:
    plant_id = plant_data["id"]

    cur.execute(
        "DELETE FROM plant_varieties WHERE plant_id = ?",
        (plant_id,)
    )

    for variety in plant_data.get("varieties", []):
        variety_id = variety.get("id")
        variety_name = variety.get("name")
        overrides = variety.get("overrides", {})
        notes = variety.get("notes")

        if not variety_id or not variety_name:
            continue

        resolved = deep_merge(plant_data, overrides)

        cur.execute(
            """
            INSERT OR REPLACE INTO plant_varieties (
                plant_id,
                variety_id,
                name,
                notes,
                overrides_json,
                resolved_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                plant_id,
                variety_id,
                variety_name,
                notes,
                json.dumps(overrides, ensure_ascii=False),
                json.dumps(resolved, ensure_ascii=False),
            )
        )


def seed_from_file(json_path: str | Path) -> None:
    json_path = Path(json_path)

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    validate_plant_json(data, source_name=str(json_path))

    with get_conn() as conn:
        cur = conn.cursor()
        insert_plant(cur, data)
        insert_companions(cur, data)
        insert_varieties(cur, data)
        conn.commit()

    print(f"Seeded: {data['id']} ({json_path.name})")


def seed_from_folder(folder_path: str | Path) -> None:
    folder = Path(folder_path)

    json_files = sorted(folder.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in {folder}")

    for json_file in json_files:
        if json_file.name == "plants_index.json":
            continue
        seed_from_file(json_file)

def seed_all_plants(plants_folder="plants"):
    folder = Path(plants_folder)
    json_files = sorted(folder.glob("*.json"))

    all_data = []

    # PASS 1: load + validate everything
    for json_file in json_files:
        if json_file.name == "plants_index.json":
            continue

        print(f"Loading {json_file.name}...")

        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        validate_plant_json(data, source_name=str(json_file))
        all_data.append((json_file, data))

    with get_conn() as conn:
        cur = conn.cursor()

        # PASS 2: insert all base plants first
        for json_file, data in all_data:
            print(f"Inserting plant {data['id']}...")
            insert_plant(cur, data)

        # PASS 3: insert companions and varieties after all plants exist
        for json_file, data in all_data:
            print(f"Inserting companions/varieties for {data['id']}...")
            insert_companions(cur, data)
            insert_varieties(cur, data)

        conn.commit()

    print("Plant seeding complete.")

if __name__ == "__main__":
    seed_from_folder("plants")