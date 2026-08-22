import math

from gardenhub.repositories.planner_layouts_repo import (
    get_planner_layout,
    save_planner_layout as persist_planner_layout,
)


LAYOUT_SCHEMA_VERSION = 1
MAX_OBJECTS = 2000
SUPPORTED_KINDS = {"plant", "bed", "irrigation", "surface", "structure", "utility"}
SUPPORTED_LAYERS = {"plants", "beds", "irrigation", "surfaces", "paths", "structures"}
SUPPORTED_KIND_LAYERS = {
    "plant": {"plants"},
    "bed": {"beds"},
    "irrigation": {"irrigation"},
    "surface": {"surfaces", "paths"},
    "structure": {"structures"},
    "utility": {"structures"},
}


class PlannerLayoutValidationError(ValueError):
    pass


def _text(value, field, maximum=160, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise PlannerLayoutValidationError(f"{field} must be text.")
    value = value.strip()
    if required and not value:
        raise PlannerLayoutValidationError(f"{field} is required.")
    if len(value) > maximum:
        raise PlannerLayoutValidationError(f"{field} is too long.")
    return value


def _number(value, field, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise PlannerLayoutValidationError(f"{field} must be a finite number.")
    value = round(float(value), 4)
    if minimum is not None and value < minimum:
        raise PlannerLayoutValidationError(f"{field} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise PlannerLayoutValidationError(f"{field} must be at most {maximum}.")
    return value


def validate_planner_layout(payload):
    if not isinstance(payload, dict):
        raise PlannerLayoutValidationError("The Planner layout must be a JSON object.")

    garden_input = payload.get("garden")
    objects_input = payload.get("objects")
    if not isinstance(garden_input, dict):
        raise PlannerLayoutValidationError("garden must be an object.")
    if not isinstance(objects_input, list):
        raise PlannerLayoutValidationError("objects must be an array.")
    if len(objects_input) > MAX_OBJECTS:
        raise PlannerLayoutValidationError(f"A plan can contain at most {MAX_OBJECTS} objects.")

    width = _number(garden_input.get("width"), "garden.width", 1, 100)
    height = _number(garden_input.get("height"), "garden.height", 1, 100)
    measurement = garden_input.get("measurement")
    units = garden_input.get("units")
    if measurement not in {"metric", "imperial", None}:
        raise PlannerLayoutValidationError("garden.measurement is not supported.")
    if units not in {"m", "ft", None}:
        raise PlannerLayoutValidationError("garden.units is not supported.")
    if measurement is None:
        measurement = "imperial" if units == "ft" else "metric"
    units = "ft" if measurement == "imperial" else "m"
    garden = {
        "name": _text(garden_input.get("name"), "garden.name", 60, required=True),
        "width": width,
        "height": height,
        "measurement": measurement,
        "units": units,
        "north": _number(garden_input.get("north", 0), "garden.north", -100000, 100000) % 360,
    }

    objects = []
    seen_ids = set()
    for index, item in enumerate(objects_input):
        prefix = f"objects[{index}]"
        if not isinstance(item, dict):
            raise PlannerLayoutValidationError(f"{prefix} must be an object.")
        object_id = _text(item.get("id"), f"{prefix}.id", 120, required=True)
        if object_id in seen_ids:
            raise PlannerLayoutValidationError(f"Duplicate object id: {object_id}.")
        seen_ids.add(object_id)
        kind = item.get("kind")
        layer = item.get("layer")
        if kind not in SUPPORTED_KINDS:
            raise PlannerLayoutValidationError(f"{prefix}.kind is not supported.")
        if layer not in SUPPORTED_LAYERS:
            raise PlannerLayoutValidationError(f"{prefix}.layer is not supported.")
        if layer not in SUPPORTED_KIND_LAYERS[kind]:
            raise PlannerLayoutValidationError(f"{prefix}.layer does not match its object kind.")
        x = _number(item.get("x"), f"{prefix}.x", 0, width)
        y = _number(item.get("y"), f"{prefix}.y", 0, height)
        object_width = _number(item.get("width"), f"{prefix}.width", 0.05, width)
        object_height = _number(item.get("height"), f"{prefix}.height", 0.05, height)
        if x + object_width > width + 0.001 or y + object_height > height + 0.001:
            raise PlannerLayoutValidationError(f"{prefix} extends outside the garden bounds.")

        cleaned = {
            "id": object_id,
            "kind": kind,
            "layer": layer,
            "name": _text(item.get("name"), f"{prefix}.name", 120, required=True),
            "x": x,
            "y": y,
            "width": object_width,
            "height": object_height,
            "rotation": _number(item.get("rotation", 0), f"{prefix}.rotation", -100000, 100000) % 360,
            "z": _number(item.get("z", index), f"{prefix}.z", -100000, 100000),
        }
        for key, maximum in (("variant", 80), ("plantId", 120), ("bedId", 120), ("zoneName", 120)):
            value = _text(item.get(key), f"{prefix}.{key}", maximum)
            if value is not None:
                cleaned[key] = value
        if kind == "plant" and "plantId" not in cleaned:
            raise PlannerLayoutValidationError(f"{prefix}.plantId is required for a plant group.")
        if kind != "plant" and "variant" not in cleaned:
            raise PlannerLayoutValidationError(f"{prefix}.variant is required for this object.")
        if "active" in item:
            if not isinstance(item["active"], bool):
                raise PlannerLayoutValidationError(f"{prefix}.active must be true or false.")
            cleaned["active"] = item["active"]
        if "quantity" in item:
            quantity = item["quantity"]
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1 or quantity > 100000:
                raise PlannerLayoutValidationError(f"{prefix}.quantity must be a positive integer.")
            cleaned["quantity"] = quantity
        if "sourcePlantingId" in item:
            source_id = item["sourcePlantingId"]
            if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id < 1:
                raise PlannerLayoutValidationError(f"{prefix}.sourcePlantingId must be a positive integer.")
            cleaned["sourcePlantingId"] = source_id
        objects.append(cleaned)

    return {"version": LAYOUT_SCHEMA_VERSION, "garden": garden, "objects": objects}


def load_planner_layout(garden_id):
    return get_planner_layout(garden_id)


def save_planner_layout(garden_id, payload):
    layout = validate_planner_layout(payload)
    updated_at = persist_planner_layout(
        garden_id,
        layout["version"],
        layout["garden"],
        layout["objects"],
    )
    return {**layout, "gardenId": garden_id, "updatedAt": updated_at}
