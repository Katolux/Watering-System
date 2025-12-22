# Project Roadmap
This document outlines the development stages of the automated irrigation system,
reflecting the current Raspberry Pi–centric architecture and data-driven design.

---

## Phase 1 – System Foundation (COMPLETED)
- Raspberry Pi set up as system coordinator
- Arduino Nano ESP32 configured as hardware controller
- Soil moisture sensors wired and readable
- Solenoid valve control via relay / MOSFET
- Single SQLite database created (garden_system.db)
- Project structure established (hardware / logic / data separation)

---

## Phase 2 – Data Acquisition Layer (COMPLETED)
- Soil moisture data acquisition from hardware sensors
- Daily weather data downloaded from Open-Meteo API
- Weather data stored locally for processing
- Clear separation between data ingestion and decision logic

---

## Phase 3 – Core Irrigation Logic (IN PROGRESS)
- Fixed base watering time per irrigation zone
- Definition of soil type coefficients
- Definition of plant type coefficients
- Water demand calculation based on:
  - Soil moisture
  - Soil coefficients
  - Plant coefficients
- Command flow: Raspberry Pi → Arduino → valves

---

## Phase 4 – Weather-Aware Modifiers (IN PROGRESS)
- Use already-ingested weather data to adjust irrigation:
  - Rain (skip or reduce watering)
  - Temperature (heat / cold adjustments)
  - Wind (evaporation factor)
- Daily aggregated weather modifiers applied to base watering logic
- Safety limits to prevent over- or under-watering

---

## Phase 5 – Data Logging & Calibration
- Log:
  - Soil moisture readings
  - Weather data
  - Watering events and durations
- Manual calibration of soil and plant coefficients
- Seasonal adjustment based on observed results
- Validation of calculated vs real soil moisture response

---

## Phase 6 – Multi-Zone & Deployment
- Multi-zone irrigation support
- Field deployment in waterproof IP67 enclosure
- Cable management and strain relief
- Long-run stability testing
- Fail-safe behavior validation (API down, Pi reboot, etc.)

---

## Phase 7 – Monitoring & Interface
- Local or web-based dashboard
- Live sensor visualization
- Manual override of irrigation
- Coefficient adjustment through UI
- System status and error reporting

---

## Phase 8 – Advanced / Optional Features
- Predictive models (ML) using historical data
- Fertilizer injection support
- Additional sensors (light, nutrients)
- Greenhouse integration
