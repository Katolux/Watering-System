from repositories import (
    get_beds_with_plants,
    get_today_moisture_slots,
    save_watering_decision,
)
from watering_decision import WateringDecision, WateringInputs
from db_access import get_today_weather
from system_events_repo import log_system_event


def daily_average_moisture_from_slots(bed_slots: dict):
    """
    bed_slots values can be either:
      - {"raw": int, "pct": int}
      - or raw int (fallback)
    Returns average RAW value as int.
    """
    if not bed_slots:
        return None

    values = []
    for v in bed_slots.values():
        if v is None:
            continue

        if isinstance(v, dict):
            raw = v.get("raw")
        else:
            raw = v

        if raw is not None:
            values.append(raw)

    if not values:
        return None

    return round(sum(values) / len(values))



def run_watering_engine():
    beds = get_beds_with_plants()
    slots_data = get_today_moisture_slots()

    # --- Weather (non-fatal) ---
    try:
        temp_max, precipitation = get_today_weather()
    except Exception as e:
        temp_max = None
        precipitation = None
        log_system_event(
            level="WARNING",
            source="watering_engine",
            message="Weather data unavailable, using neutral modifiers",
            details=str(e)
        )

    decision_engine = WateringDecision()

    for bed in beds:
        (
            bed_id,
            active,
            plant_name,
            min_m,
            max_m,
            base_minutes,  # FROM PLANT CONFIG
        ) = bed

        if not active:
            continue

        bed_slots = slots_data.get(bed_id, {})
        avg_moisture = daily_average_moisture_from_slots(bed_slots)

        if avg_moisture is None:
            continue

        inputs = WateringInputs(
            base_minutes=base_minutes,
            avg_moisture=avg_moisture,
            min_moisture=min_m,
            max_moisture=max_m,
            temp_max=temp_max,
            precipitation=precipitation,
        )

        final_minutes, breakdown = decision_engine.calculate(inputs)

        save_watering_decision(
            bed_id=bed_id,
            plant_name=plant_name,
            avg_moisture=avg_moisture,
            temp_max=temp_max,
            precipitation=precipitation,
            base_minutes=base_minutes,
            final_minutes=final_minutes,
            soil_factor=breakdown["soil_factor"],
            temp_factor=breakdown["temp_factor"],
            rain_factor=breakdown["rain_factor"],
        )
