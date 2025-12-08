# Project Roadmap

This file outlines the planned development stages for the watering system.

---

## Phase 1 – Core System (IN PROGRESS)
- Basic moisture reading
- DHT22 temperature & humidity
- Manual watering controls
- Pump activation via relay
- Basic main.ino and sensors.ino

---

## Phase 2 – Smart Logic
- Moisture thresholds
- Temperature adjustments
- Basic rain prediction
- Safety delays

---

## Phase 3 – Weather Integration
Python (Raspberry Pi):
- Retrieve hourly and daily forecast from Open-Meteo
- Extract temperature, humidity, rain probability, precipitation, cloud cover, sunshine duration, wind speed
- Process data using get_weather.py
- Provide simplified JSON output for Arduino/ESP

Arduino / ESP:
- Read simplified JSON forecast
- Adjust irrigation logic based on weather

---

## Phase 4 – Advanced Irrigation Logic
Environmental factors:
- Temperature (adjust watering on heat/cold)
- Wind (evaporation)
- Sunshine duration
- Rain probability

Soil factors:
- Clay, loam, sand behavior
- Retention and absorption speed

Plant factors:
- Water requirements per species

Combined formula:
base_time × temperature_factor × wind_factor × soil_factor × plant_factor

---

## Phase 5 – Data Logging and Dashboard
- Log moisture and weather
- Log watering events
- Display live sensor data
- Manual watering from dashboard
- Adjustable thresholds

---

## Phase 6 – Deployment and Stabilisation
- Waterproof housing
- Cable routing
- Multi-zone support
- Field calibration

---

## Phase 7 – Optional Features
- Fertilizer injection
- Light sensor
- Soil nutrients
- Greenhouse integration

