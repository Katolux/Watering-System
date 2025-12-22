# System Overview

This document describes the high-level architecture of the automated watering system.

---

## Purpose

The goal of this project is to automate irrigation in a 70 m² garden using real-time sensor data and daily weather data.  
The system helps reduce water waste, improve soil health, and protect plants from heat, wind, or drought stress.

---

## Core System Components

1. Soil moisture monitoring (capacitive sensors)
2. Optional environmental monitoring (future expansion)
3. Optional water-tank level detection
4. Solenoid valve control via relay or MOSFET module
5. Weather data integration (Open-Meteo API, daily aggregates)
6. Smart irrigation logic that considers:
   - Soil moisture
   - Soil type
   - Plant type
   - Temperature
   - Wind
   - Rain probability and precipitation
7. Automated sensor collection (multiple times per day)
8. Automatic recovery in case of sensor or API failure



---

## High-Level Architecture

The system has four major layers:

1. **Sensor Layer**  
Reads environmental data from the Arduino sensor hub:

- Soil moisture  
- (Optional) environmental sensors (future)

Data is delivered to the Raspberry Pi in JSON format.  
Failed readings never block watering—the system uses the last valid record.



2. **Weather Layer**  
Retrieves daily aggregated weather data from Open-Meteo, including:

- Rain probability  
- Precipitation  
- Temperature  
- Wind speed  

Weather is refreshed automatically once per day.

If the request fails:
- The system retries once  
- If it still fails, it uses the last valid forecast and logs the issue
 


3. **Logic Layer**  
Calculates watering duration based on:
- Soil moisture ranges
- Weather-derived modifiers
- Soil type coefficients
- Plant type coefficients
- Wind-adjusted evaporation rate
- Heat and cold protection rules

4. **Sensor Reliability Logic**  
Sensor readings are advisory and never block irrigation.

Rules:
- A single failed reading is ignored  
- A failed cycle logs the error and uses the last valid data  
- Moisture sensors influence watering duration, not whether watering occurs  
- API failures fall back to the previous forecast  


5. **Actuator Layer**  
Controls irrigation cycles, valve run-times, and safety shutdowns.


---

## Architecture Diagram (ASCII)
~~~
                 ┌───────────▼──────────┐
                 │   Weather API (Pi)   │
                 │  Open-Meteo Forecast │
                 └───────────┬──────────┘
                             │ JSON
                ┌────────────▼────────────┐
                │   Weather Logic Layer   │
                │ (wind, rain, temp)      │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │  Irrigation Logic Layer │
                │  (soil type + plant)    │
                └────────────┬────────────┘
                             │
     ┌───────────────────────┼────────────────────────┐
     ▼                       ▼                        ▼
Sensors Layer        Actuator Layer             Safety Systems
(moisture, temp)     (relay, valves)          (tank, cooldown, errors)
~~~
---
## Automated Processes Summary

### Daily processes
- Weather API update  
- Sensor reading cycles  
- Daily state calculation  
- Automatic irrigation if needed  

### User-triggered processes
- Manual sensor reading  
- Manual watering  
- Viewing history  

### Safety behaviors
- Fallback on API failure  
- Fallback on sensor failure  
- Optional tank-protection logic  
- Temperature/wind irrigation restrictions  


## System Philosophy

The watering system aims to behave like a good gardener:
- It waters based on plant needs, not on fixed timers.
- It avoids watering before rain.
- It reduces watering if soil holds moisture well.
- It increases watering in heat or wind.
- It updates decisions based on daily conditions and recent sensor data.

This document will expand as more features are added.
