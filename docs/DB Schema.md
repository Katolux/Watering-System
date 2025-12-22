## Database Schema

---

This project uses a single SQLite database to store all persistent data related to weather, sensors, irrigation events, and configuration.

Database file: garden_system.db  
- Database type: SQLite  
- Design principle: simple, append-only where possible, aligned with real system behaviour  
- Time handling: all timestamps are generated explicitly in Python (UTC, ISO 8601)  

The database does not generate or modify timestamps.

---

## Overview

The database is designed to support:

- Daily weather ingestion and historical storage  
- Time-series sensor data (after calibration)  
- Irrigation event logging  
- Soil and plant configuration via coefficients  
- Future ML experimentation based on real historical data  

At the current stage of the project, only the weather table is fully implemented and populated.  
Other tables are planned and documented here for architectural clarity.

---

## Weather Data

- Table: weather_data  

This table stores daily aggregated weather forecasts downloaded from the Open-Meteo API.

### Purpose

- Provide daily weather modifiers for irrigation logic  
- Preserve ingestion order for ML experimentation  
- Maintain a local historical weather record independent of the API  

### Columns

timestamp      TEXT  
date           TEXT  
temp_max       REAL  
temp_min       REAL  
precipitation  REAL  
sunshine       REAL  
daylight       REAL  
wind_max       REAL  
wind_dir       REAL  

### Field semantics

timestamp  
UTC timestamp (ISO 8601) generated in Python at insertion time.  
Represents when the record was stored, not the forecasted day.

date  
Calendar date the forecast applies to (YYYY-MM-DD).

temp_max / temp_min  
Daily maximum and minimum air temperature (°C).

precipitation  
Total daily precipitation (mm).

sunshine  
Sunshine duration in minutes.

daylight  
Total daylight duration in minutes.

wind_max  
Maximum daily wind speed.

wind_dir  
Dominant daily wind direction (degrees).

### Notes

- Weather data is append-only  
- Records are never overwritten  
- Ordering by insertion (rowid) reflects download order and is used by ML pipelines  
- Only daily aggregated data is stored (no hourly forecasts)  

---

## Sensor Readings (Planned)

- Table: sensor_readings  

This table will store timestamped soil moisture readings once sensors are calibrated and deployed.

### Purpose

- Persist soil moisture history  
- Support calibration, debugging, and ML  
- Correlate soil state with weather and irrigation events  

### Columns

id            INTEGER PRIMARY KEY AUTOINCREMENT  
sensor_id     TEXT  
zone_id       TEXT  
soil_moisture REAL  
timestamp     TEXT  

### Notes

- timestamp is generated in Python (UTC, ISO 8601)  
- Readings will be averaged over a short sampling window before insertion  
- Invalid or failed readings are not stored  
- Final scaling depends on sensor calibration  

---

## Watering Events (Planned)

- Table: watering_events  

This table will log every irrigation action executed by the system.

### Purpose

- Audit irrigation behaviour  
- Support debugging and validation  
- Enable correlation between watering, sensors, and weather  

### Columns

id               INTEGER PRIMARY KEY AUTOINCREMENT  
zone_id          TEXT  
duration_minutes REAL  
reason           TEXT  
executed_at      TEXT  

### Notes

- executed_at is generated in Python (UTC)  
- reason may include:  
  - auto  
  - manual  
  - rain_skip  
  - heat_adjustment  
  - safety_limit  
- Append-only table  

---

## Soil Profiles (Planned)

- Table: soil_profiles  

Stores soil behaviour coefficients used by irrigation calculations.

### Purpose

- Model soil retention and drainage behaviour  
- Allow empirical calibration without code changes  

### Columns

soil_id     TEXT PRIMARY KEY  
description TEXT  
soil_factor REAL  

### Notes

- soil_factor is a multiplier applied to watering duration  
- Values are calibrated empirically  
- Assumes drip irrigation
### Table: `weather_data`

This table stores **daily aggregated weather forecasts** downloaded from the Open-Meteo API.

### Purpose

- Provide daily weather modifiers for irrigation logic
- Preserve ingestion order for ML experimentation
- Maintain a local historical weather record independent of the API

### Columns

```text
timestamp      TEXT
date           TEXT
temp_max       REAL
temp_min       REAL
precipitation  REAL
sunshine       REAL
daylight       REAL
wind_max       REAL
wind_dir       REAL


Field semantics
timestamp
UTC timestamp (ISO 8601) generated in Python at insertion time.
Represents when the record was stored, not the forecasted day.
date
Calendar date the forecast applies to (YYYY-MM-DD).
temp_max / temp_min
Daily maximum and minimum air temperature (°C).
precipitation
Total daily precipitation (mm).
sunshine
Sunshine duration in minutes.
daylight
Total daylight duration in minutes.
wind_max
Maximum daily wind speed.
wind_dir
Dominant daily wind direction (degrees).
Notes
Weather data is append-only
Records are never overwritten
Ordering by insertion (rowid) reflects download order and is used by ML pipelines
Only daily aggregated data is stored (no hourly forecasts)
Sensor Readings (Planned)
Table: sensor_readings
This table will store timestamped soil moisture readings once sensors are calibrated and deployed.
Purpose
Persist soil moisture history
Support calibration, debugging, and ML
Correlate soil state with weather and irrigation events
Columns
Copy code

id            INTEGER PRIMARY KEY AUTOINCREMENT
sensor_id     TEXT
zone_id       TEXT
soil_moisture REAL
timestamp     TEXT
Notes
timestamp is generated in Python (UTC, ISO 8601)
Readings will be averaged over a short sampling window before insertion
Invalid or failed readings are not stored
Final scaling depends on sensor calibration
Watering Events (Planned)
Table: watering_events
This table will log every irrigation action executed by the system.
Purpose
Audit irrigation behaviour
Support debugging and validation
Enable correlation between watering, sensors, and weather
Columns
Copy code

id               INTEGER PRIMARY KEY AUTOINCREMENT
zone_id          TEXT
duration_minutes REAL
reason           TEXT
executed_at      TEXT
Notes
executed_at is generated in Python (UTC)
reason may include:
auto
manual
rain_skip
heat_adjustment
safety_limit
Append-only table
Soil Profiles (Planned)
Table: soil_profiles
Stores soil behaviour coefficients used by irrigation calculations.
Purpose
Model soil retention and drainage behaviour
Allow empirical calibration without code changes
Columns
Copy code

soil_id     TEXT PRIMARY KEY
description TEXT
soil_factor REAL
Notes
soil_factor is a multiplier applied to watering duration
Values are calibrated empirically
Assumes drip irrigation
Plant Profiles (Planned)
Table: plant_profiles
Stores plant-specific watering preferences.
Purpose
Adjust watering demand based on plant type
Avoid hard-coded plant logic
Columns
Copy code

plant_id             TEXT PRIMARY KEY
description          TEXT
plant_factor         REAL
moisture_target_low  REAL
moisture_target_high REAL
Notes
Plants influence watering via coefficients and target moisture bands
Plants do not redefine soil physics
Irrigation Zones (Planned)
Table: irrigation_zones
Links physical irrigation zones to soil and plant profiles.
Purpose
Decouple physical layout from irrigation logic
Support multi-zone expansion
Columns
Copy code

zone_id  TEXT PRIMARY KEY
soil_id  TEXT
plant_id TEXT
Design Principles
One database for the entire system
Explicit timestamps generated in Python
Append-only historical data
No reliance on database-generated time
Schema evolves from real system behaviour
Current Status
weather_data is implemented and populated
Sensor hardware is under calibration
Remaining tables will be added once:
sensor ranges are validated
hardware is deployed
end-to-end readings are confirmed
