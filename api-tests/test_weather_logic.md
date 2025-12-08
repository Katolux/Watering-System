# Weather Logic Test Cases

## Case 1: Rain Expected
- Rain probability: 80%
- Soil moisture: LOW
- Temperature: 19°C
### Expected:
Skip watering completely.

---

## Case 2: Windy Afternoon
- Wind speed: 22 km/h
- Temperature: 20°C
- Soil moisture: LOW
### Expected:
Increase watering duration (evaporation increases).

---

## Case 3: Dry Soil + Hot Weather
- Soil moisture: LOW
- Temperature: 32°C
- Wind: mild
### Expected:
Large watering multiplier (heat stress + evaporation).

---

## Case 4: Cold + Moist Soil
- Temperature: 7°C
- Soil moisture: MEDIUM or HIGH
### Expected:
Reduce or skip watering.

---

## Case 5: Soil Type Variation
### Clay Soil:
- Moisture increases slowly, holds water long
### Expected:
Reduce watering time.

### Sandy Soil:
- Moisture drains quickly
### Expected:
Increase watering time.

---

## Case 6: Plant Type Variation
### Tomato:
- Needs stable moisture
### Expected:
Higher base watering.

### Rosemary:
- Avoid overwatering
### Expected:
Lower base watering.

