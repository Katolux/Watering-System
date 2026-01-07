# Garden System – Python Backend (v1 Beta)

This directory contains the **Python backend** of the Garden System.

It is responsible for:
- ingesting sensor data from Arduino devices
- storing and organizing data in SQLite
- exposing a web-based management UI
- computing watering decisions (v1 beta)

This backend is designed to run on a **Raspberry Pi** as the central system controller.

---

## Responsibilities

The Python backend handles:

- Sensor ingestion via Flask HTTP API
- Slot-based aggregation of daily moisture readings
- Database management (SQLite, UTC timestamps)
- Bed, plant, and sensor configuration via web UI
- Watering decision computation (not execution)

Actual hardware control (valves, relays) remains on the Arduino side.

---

## Architecture Overview
Arduino / ESP32
↓ HTTP POST (sensor readings)
Flask Receiver
↓
SQLite Database
↓
Web UI / Watering Logic

---


Key design decisions:
- Sensor identity (`sensor_id`) is stable
- Bed assignment is dynamic
- Sensors can be moved without losing historical meaning
- Multiple daily measurements are aggregated using slots

---

## File Overview
```
garden_system/
├─ app.py # Flask application and UI routes
├─ python_receiver_final.py # Production sensor ingestion endpoint
├─ db.py # Centralized DB connection handling
├─ db_schema.py # SQLite table definitions and constraints
├─ db_init.py # Database initialization
├─ repositories.py # Data access layer (pure SQL)
├─ watering_engine.py # Watering decision engine (v1 beta)
├─ watering_decision.py # Pure decision logic
├─ templates/ # HTML templates
└─ static/ # Static assets (CSS, JS)
```
---

## Database Notes

- All timestamps are stored in UTC
- Daily measurements are grouped using **slots**
- Sensor readings are unique per:
    - (sensor_id, date, slot)


This prevents duplicate data and supports safe retries from hardware.

---

## Watering Logic (v1 Beta)

The watering engine computes **recommended watering durations** based on:

- Daily averaged soil moisture
- Plant moisture thresholds
- Weather data (temperature, precipitation)
- Fixed base watering time (configurable later)

⚠️ Important:
- Decisions are **calculated and stored**
- Watering is **not automatically executed**
- This logic is intended for supervised testing

---

## Current Status

- Receiver and database layers are stable
- UI reflects live and historical data
- Watering logic is available for testing
- Raspberry Pi deployment is the next step

---

## Notes

This backend is part of an evolving system.
The emphasis is on **clean architecture, correctness, and extensibility** rather than premature automation.





