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

---

Sensor Reading Logic

The system collects soil and air data automatically several times each day.

START  
    ↓  
Attempt to read JSON from Arduino  
    ↓  
Connection OK?  
    ├─ No → Log error  
    │       Use last valid readings  
    │       END  
    ↓ Yes  
Collect readings for 5 seconds  
    ↓  
Valid readings found?  
    ├─ No → Retry once  
    │       ↓  
    │     Retry valid?  
    │         ├─ No → Log error → END  
    │         └─ Yes → Continue  
    ↓ Yes  
Compute averages (moisture, soil_temp, air_temp, humidity)  
    ↓  
Save record to database (SQLite)  
    ↓  
END

---

Weather Update Logic

The weather forecast updates once per day automatically.

START (daily)  
    ↓  
Request forecast from Open-Meteo API  
    ↓  
Success?  
    ├─ Yes → Save data to SQLite → END  
    ↓ No  
Retry once  
    ↓  
Retry success?  
    ├─ Yes → Save data → END  
    └─ No → Log failure  
           Use last valid forecast  
           END

---

Manual Sensor Read Logic

User selects "Read sensors now"  
    ↓  
Perform a single 5-second reading cycle  
    ↓  
Save to history + display measurements  
    ↓  
END

---

These diagrams will grow as the system evolves.

Watering Calculation – Mathematical Model (Draft)

This section defines the mathematical interpretation of the logic rules applied by the watering system.
All calculations are expressed in metric units and are designed to be configurable per climate, soil, and irrigation system.

Reference Values

Base watering time
T_base = reference watering duration (e.g. 45 minutes)

This represents:

normal weather

reference soil mix

adequate soil moisture

no rainfall influence

All adjustments are relative to T_base.

Temperature Adjustment

Temperature affects evapotranspiration rate (ET) and plant water demand.

Let:

T_air = average air temperature (°C)

K_temp = temperature coefficient

Example logic:

IF T_air ≥ T_hot:
    K_temp = 1 + α_hot
ELIF T_air ≤ T_cold:
    K_temp = 1 − α_cold
ELSE:
    K_temp = 1.0


Where:

α_hot = proportional increase due to heat stress (e.g. +0.10 → +10%)

α_cold = proportional reduction due to low ET (e.g. −0.10 → −10%)

Temperature does not directly determine watering time; it modifies demand.

Wind Adjustment

Wind increases evaporation at the soil surface and leaf boundary layer.

Let:

V_wind = average wind speed (m/s or km/h)

K_wind = wind evaporation coefficient

Example:

IF V_wind ≥ strong_wind_limit:
    K_wind = 1 + β_high
ELIF V_wind ≥ mild_wind_limit:
    K_wind = 1 + β_medium
ELSE:
    K_wind = 1.0


Where:

β_high > β_medium > 0

Wind never reduces watering, only increases evaporative loss.

Soil Moisture Adjustment (Sensor-Based)

Soil moisture sensors provide direct feedback on the current state of the root zone.

Let:

M_soil = averaged soil moisture reading

M_target = acceptable moisture band (defined per soil)

ΔT_moisture = time adjustment based on deviation from target

Conceptually:

IF M_soil < M_target_low:
    ΔT_moisture > 0
ELIF M_soil > M_target_high:
    ΔT_moisture < 0
ELSE:
    ΔT_moisture = 0


This adjustment is additive, not multiplicative, because it reflects how far the soil is from equilibrium.

Soil-Type Coefficient (Drip Irrigation)

Soil type determines:

infiltration rate

water retention

depth and shape of the wetted bulb under drip irrigation

Let:

K_soil = soil water coefficient

This coefficient represents the relative irrigation volume required to restore the effective root zone moisture under the same system and conditions.

Typical interpretation:

Soil Type	Physical Behavior	K_soil
Sandy / fast-draining	Deep percolation, low retention	> 1.0
Balanced loam / compost	Reference behavior	≈ 1.0
Heavy / high-retention	Slow drainage, high retention	< 1.0

Application:

T_after_soil = T_before_soil × K_soil


This coefficient is intended to be calibrated experimentally for each soil mix using the installed drip system.

Rainfall Adjustment

Rain contributes to soil water storage.

Let:

R_24h = rainfall in last 24 hours (mm)

ΔT_rain = time reduction due to rainfall

Example:

IF R_24h ≥ heavy_rain_threshold:
    ΔT_rain = −γ_high
ELIF R_24h ≥ light_rain_threshold:
    ΔT_rain = −γ_low
ELSE:
    ΔT_rain = 0


Rain adjustments are additive reductions, not multipliers.

Combined Watering Formula

Putting all components together:

T_adjusted =
(
    T_base
    + ΔT_moisture
    + ΔT_rain
)
× K_temp
× K_wind
× K_soil


Where:

T_adjusted = final watering duration (minutes)

A lower bound is enforced:

T_final = max(T_adjusted, 0)

Conversion to Volume (Hardware Layer)

Let:

Q = system flow rate (L/min)

Then:

Water volume (L) = T_final × Q


Time-based control is therefore a proxy for volumetric irrigation.

Notes on Plants

Plants influence watering indirectly, through:

preferred soil type

target moisture bands

tolerance to stress

Plant logic modifies:

moisture thresholds

acceptable depletion range

It does not redefine soil physics or base watering time.

Calibration Philosophy

Coefficients are:

initially estimated

later validated empirically

eventually learned or refined using historical data and ML

The logic is designed so that coefficients can evolve without rewriting the system.
