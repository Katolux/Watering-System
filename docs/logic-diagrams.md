~~~ 
Logic Diagrams  
This document outlines the decision-making process of the watering system.

---

Moisture-Based Watering Logic

IF soil_moisture < moisture_threshold:
    CHECK weather
    IF rain_probability >= rain_limit:
        SKIP watering
    ELSE:
        APPLY adjustments (temp, wind, soil type, plant type)
        WATER for calculated_duration
ELSE:
    DO NOT water

---

Temperature Adjustment Logic

IF temperature > heat_limit:
    factor = HOT_INCREASE_MULTIPLIER
ELIF temperature < cold_limit:
    factor = COLD_REDUCTION_MULTIPLIER
ELSE:
    factor = 1.0

---

Wind Adjustment Logic

IF wind_speed >= strong_wind_limit:
    evaporation_factor = HIGH
ELIF wind_speed >= mild_wind_limit:
    evaporation_factor = MEDIUM
ELSE:
    evaporation_factor = LOW

Wind increases evaporation → more watering.
No wind → soil holds moisture longer.

---

Soil-Type Logic (future)

IF soil_type == "clay":
    water_absorption = SLOW
    retention = HIGH
    watering_time = watering_time * 0.8

ELIF soil_type == "sandy":
    water_absorption = FAST
    retention = LOW
    watering_time = watering_time * 1.3

ELIF soil_type == "loam":
    water_absorption = MEDIUM
    retention = MEDIUM

---

Plant-Type Logic (future)

IF plant_type == "tomato":
    moisture_requirement = HIGH

ELIF plant_type == "rosemary":
    moisture_requirement = LOW

ELIF plant_type == "lettuce":
    moisture_requirement = VERY_HIGH

Plant profiles modify thresholds.

---

Combined Watering Calculation

Final watering duration =
    base_time
    × temperature_factor
    × wind_factor
    × soil_factor
    × plant_factor

---

Tank Protection Logic

IF tank_level == LOW:
    PUMP OFF
    BLOCK irrigation
    ALERT user (future)

These diagrams will grow as the system evolves.
~~~ 
