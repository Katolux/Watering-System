# System Overview

This document describes the high-level architecture of the automated watering system.

---

## Purpose

The goal of this project is to automate irrigation in a 70 m² garden using real-time sensor data and weather forecasting.  
The system helps reduce water waste, improve soil health, and protect plants from heat or drought stress.

---

## Core System Components

1. Soil moisture monitoring (capacitive sensors)
2. Temperature & humidity monitoring (DHT22)
3. Optional water-tank level detection
4. Pump or solenoid control via relay module
5. Weather forecast integration (Open-Meteo API)
6. Smart irrigation logic that considers:
   - Soil hydration
   - Soil type (future)
   - Plant type (future)
   - Temperature & humidity
   - Wind
   - Rain probability and precipitation
   - Sunshine duration

---

## High-Level Architecture

The system has four major layers:

1. **Sensor Layer**  
   Reads soil moisture, temperature, humidity, wind (via API), etc.

2. **Weather Layer**  
   Fetches hourly and daily weather from Open-Meteo.  
   This will run first on Python (Raspberry Pi), and later in simplified form on Arduino/ESP.

3. **Logic Layer**  
   Makes decisions based on:
   - Soil moisture thresholds
   - Weather predictions
   - Soil and plant profiles
   - Wind-adjusted evaporation rate
   - Heat or cold protection rules

4. **Actuator Layer**  
   Controls irrigation cycles, pump run-times, and safety shutdowns.

---

## Architecture Diagram (ASCII)

                 ┌───────────▼──────────┐
                 │   Weather API (Pi)   │
                 │  Open-Meteo Forecast │
                 └──────────┬───────────┘
                            │ JSON
                ┌───────────▼─────────────┐
                │   Weather Logic Layer   │
                │  (wind, sun, rain, temp)│
                └───────────┬─────────────┘
                            │
                ┌───────────▼─────────────┐
                │  Irrigation Logic Layer │
                │ (soil type + plant type)│
                └───────────┬─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  Sensors Layer       Actuator Layer       Safety Systems
 (moisture, temp)     (relay, pump)       (tank, cooldown)






---

## System Philosophy

The watering system aims to behave like a good gardener:
- It waters based on plant needs, not on fixed timers.
- It avoids watering before rain.
- It reduces watering if soil holds moisture well.
- It increases watering in heat or wind.
- It updates decisions hourly based on forecast changes.

This document will expand as more features are added.
