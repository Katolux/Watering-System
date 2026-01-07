from datetime import datetime
from garden_config import (
    get_beds_with_plants,
    get_today_moisture_slots,
    save_watering_decision,
)
from watering_decision import WateringDecision, WateringInputs
from db_access import get_today_weather

def run_watering_engine():
    beds = get_beds_with_plants()
    slots_data = get_today_moisture_slots()
    temp_max, precipitation = get_today_weather()

    decision_engine = WateringDecision()

    for bed_id, active, plant_name, min_m, max_m in beds:
        if not active:
            continue

        bed_slots = slots_data.get(bed_id, {})
        avg_moisture = daily_average_moisture_from_slots(bed_slots)

        inputs = WateringInputs(
            base_minutes=45,  # later from plant
            avg_moisture=avg_moisture,
            min_moisture=min_m,
            max_moisture=max_m,
            temp_max=temp_max,
            precipitation=precipitation
        )

        final_minutes, breakdown = decision_engine.calculate(inputs)

        save_watering_decision(
            bed_id=bed_id,
            plant_name=plant_name,
            avg_moisture=avg_moisture,
            temp_max=temp_max,
            precipitation=precipitation,
            base_minutes=inputs.base_minutes,
            final_minutes=final_minutes,
            soil_factor=breakdown["soil_factor"],
            temp_factor=breakdown["temp_factor"],
            rain_factor=breakdown["rain_factor"]
        )


if __name__ == "__main__":
    run_watering_engine()
