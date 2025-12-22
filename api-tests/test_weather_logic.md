## Weather & Irrigation Logic – Test Scenarios

This document defines expected behavior for the irrigation calculation logic.
All values assume daily aggregated weather data and coefficient-based modifiers.

---

## Case 1: High Rain Probability
Inputs:
- Rain probability (daily): 80%
- Soil moisture: LOW
- Temperature (daily max): 19°C

Expected behavior:
- Rain modifier strongly reduces watering
- Final watering time reduced to zero or minimum safety threshold

---

## Case 2: High Wind Day
Inputs:
- Wind speed (daily max): 22 km/h
- Temperature (daily max): 20°C
- Soil moisture: LOW

Expected behavior:
- Wind evaporation modifier increases watering time
- Increase remains capped within safety limits

---

## Case 3: Dry Soil + Heat Stress
Inputs:
- Soil moisture: LOW
- Temperature (daily max): 32°C
- Wind: mild

Expected behavior:
- Heat and soil modifiers combine
- High watering multiplier applied
- Final duration limited by max watering cap

---

## Case 4: Cold Day + Moist Soil
Inputs:
- Temperature (daily max): 7°C
- Soil moisture: MEDIUM or HIGH

Expected behavior:
- Cold modifier reduces water demand
- Watering reduced or skipped entirely

---

## Case 5: Soil Type Influence

# Clay soil:
- High retention coefficient
Expected behavior:
- Slower moisture decay
- Reduced watering time compared to neutral soil

# Sandy soil:
- Low retention coefficient
Expected behavior:
- Faster moisture loss
- Increased watering time

---

## Case 6: Plant Type Influence

Tomato:
- High water demand coefficient
Expected behavior:
- Higher base watering requirement
- Strong response to heat stress

Rosemary:
- Low water demand coefficient
Expected behavior:
- Reduced base watering
- Aggressive overwatering prevention

