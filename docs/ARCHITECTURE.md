# GardenHUB Architecture

## System Summary

GardenHUB is a Flask and SQLite garden-management and irrigation system. It ingests soil-moisture readings from Arduino/ESP32 nodes, stores readings and weather in SQLite, produces explainable watering recommendations, and exposes configuration and monitoring through a Jinja-based web interface.

Current actuation is dry-run/logging only.

Future actuation may use valve control and flow-based volume delivery.

---

## High-Level Runtime Flow

```text
Arduino / ESP32
    |
    | HTTP POST /sensor_data
    v
Receiver Blueprint
    |
    v
Sensor repositories
    |
    v
SQLite

Browser
    |
    v
Flask routes / Blueprints
    |
    v
Repositories and services
    |
    +--> SQLite
    +--> Jinja templates

scheduler.py
    |
    +--> weather refresh
    |
    +--> watering engine
            |
            +--> watering decisions
            +--> system events
```

---

## Current Git/Refactor State

Current structural branch:

```text
v1.3-structure-review
```

Completed:

- Phase 1: database modules moved into `gardenhub/db/`
- Phase 2A: system-events repository moved into `gardenhub/repositories/`
- Phase 2B: weather database access moved into `gardenhub/repositories/weather_repo.py`
- Phase 2C: bed persistence and bed/plant aggregation moved into `gardenhub/repositories/beds_repo.py`
- Phase 2D: sensor metadata and sensor-reading persistence moved into `gardenhub/repositories/sensors_repo.py`
- Phase 2E: watering-decision and watering-event persistence moved into `gardenhub/repositories/watering_repo.py`
- Phase 2F: plant, variety, companion, and plant JSON persistence moved into `gardenhub/repositories/plants_repo.py`
- Phase 2: repository split complete; the transitional root `repositories.py` has been removed
- Phase 3A: calibration moved unchanged into `gardenhub/services/calibration.py`
- Phase 3B: garden status logic moved unchanged into `gardenhub/services/garden_status.py`
- Phase 3C: watering-decision logic moved unchanged into `gardenhub/services/watering_decision.py`

Current structural direction:

- database modules under `gardenhub/db/`
- repository modules under `gardenhub/repositories/`
- route modules under `gardenhub/routes/`
- service/domain modules under `gardenhub/services/`
- top-level product assets and operational folders remain at root

---

## Current Repository Structure

```text
ProjectGarden/
├── app.py
├── scheduler.py
├── requirements.txt
├── README.md
├── arduino_send_final.cpp
├── arduino_secrets.example.h
│
├── gardenhub/
│   ├── __init__.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── initialization.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── beds_repo.py
│   │   ├── plants_repo.py
│   │   ├── sensors_repo.py
│   │   ├── system_events_repo.py
│   │   ├── watering_repo.py
│   │   └── weather_repo.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── calibration.py
│   │   ├── garden_status.py
│   │   └── watering_decision.py
│   │
│   └── routes/
│       ├── __init__.py
│       ├── automation_routes.py
│       ├── plant_routes.py
│       ├── sensor_routes.py
│       └── watering_routes.py
│
├── db_access.py
├── get_weather_new.py
├── historic_weather.py
├── python_receiver.py
├── watering_engine.py
├── ml_pipeline.py
│
├── seeding/
├── plants/
├── templates/
├── static/
├── docs/
└── dev_tests/
    └── legacy/
        ├── README.md
        └── historic_sensor.py
```

This remains a transitional structure for service and route modules. The repository package split is complete and no active repository module remains at the project root.

---

## Flask Application

### `app.py`

Current responsibilities:

- create the Flask application
- register five Blueprints
- initialize database tables
- conditionally refresh weather
- define:
  - `GET /`
  - `POST /refresh_weather`
  - `GET /history`

`app.py` is already small. It remains the Flask constructor and owner of the three un-namespaced routes during the current refactor.

No application factory will be introduced during this structural pass.

### Registered Blueprints

- `receiver`
- `automation`
- `sensor`
- `watering`
- `plant`

Endpoint names and Blueprint namespaces are used extensively by templates and must remain unchanged during structural work.

---

## Sensor Ingestion

Current route:

```text
POST /sensor_data
```

Current flow:

1. Arduino posts:
   - `bed`
   - `sensor`
   - `moisture`
2. Missing or invalid fields return `400`.
3. Readings at or above the out-of-soil threshold return `202` without persistence.
4. Accepted raw readings are converted to percentage.
5. The next daily slot is assigned.
6. The reading is stored in `sensor_readings`.
7. A seventh daily reading returns `409`.

Current slot assignment is bed-based and limited to slots 1–6.

This behavior must remain unchanged during the structural refactor.

---

## Database

Connection and schema modules now live under:

```text
gardenhub/db/
```

### `connection.py`

- defines the project-root SQLite path
- creates connections
- enables foreign keys
- uses the current timeout and thread settings

### `schema.py`

Contains idempotent table-creation functions, including weather table initialization.

### `initialization.py`

Calls the table initialization functions in the existing order.

### Current application tables

- `zones`
- `beds`
- `sensors`
- `plants`
- `plant_varieties`
- `plant_companions`
- `bed_plantings`
- `sensor_readings`
- `weather_data`
- `watering_decisions`
- `watering_events`
- `system_events`

Development databases are disposable while schema and data models are still evolving.

---

## Repositories

Current packaged repositories:

- `beds_repo.py` owns bed creation, bed retrieval, plant assignment to beds, and bed/plant watering-configuration aggregation.
- `plants_repo.py` owns plant catalog retrieval, full plant lookup and existence checks, rich plant insertion and updating, plant deletion cleanup, variety lookup/existence/insertion/deletion, companion retrieval, and JSON-field serialization for plant persistence.
- `sensors_repo.py` owns sensor creation and retrieval, sensor-to-bed assignment, the bed/sensor diagnostic listing, reading-slot selection, sensor-reading persistence, today's moisture-slot aggregation, and recent-reading retrieval.
- `weather_repo.py` owns weather persistence, stored-weather freshness, and weather retrieval queries.
- `watering_repo.py` owns saving watering decisions, retrieving the latest decision for a bed, logging watering events, and retrieving recent watering-event history.
- `system_events_repo.py` owns system-event persistence and retrieval.

The transitional root `repositories.py` was removed after Phase 2F because no active repository functions remained. Active runtime callers import the packaged domain repositories directly; no compatibility re-export is used.

The obsolete standalone `historic_sensor.py` is retained unchanged under `dev_tests/legacy/` and is not imported by the active runtime.

---

## Calibration Service

`gardenhub/services/calibration.py` owns the current soil-moisture calibration constants, the out-of-soil raw threshold, and the raw-to-percentage conversion helper.

Current consumers:

- `python_receiver.py` uses `OUT_OF_SOIL_RAW` and `raw_to_pct()` to preserve receiver filtering and stored percentage values.
- `gardenhub/routes/automation_routes.py` uses `raw_to_pct()` for legacy raw-only slot values.
- `watering_engine.py` uses `raw_to_pct()` for legacy raw-only slot values before calculating daily average moisture.

The file is byte-identical to the former root `calibration.py`. The root module was removed and no compatibility copy or re-export remains.

---

## Garden Status Service

`gardenhub/services/garden_status.py` owns the existing moisture-status interpretation, overall bed-status summary, and daily-average helper logic.

Current consumer:

- `gardenhub/routes/automation_routes.py` uses `moisture_status()` and `overall_bed_status()` to preserve the moisture labels and bed summaries displayed by `/automation/beds`.

The module's function signatures and bodies remain equivalent to the former root `garden_logic.py`. The unused `daily_average_moisture()` helper remains preserved, the root module was removed, and no compatibility copy or re-export remains.

---

## Watering Decision Service

`gardenhub/services/watering_decision.py` owns the existing watering-input dataclass, soil-moisture factor, temperature factor, rain factor, and final minutes-based watering calculation.

Current consumer:

- `watering_engine.py` creates `WateringInputs`, runs `WateringDecision.calculate()`, and persists the returned final minutes and soil, temperature, and rain factors.

The module's dataclass fields, class and function signatures, thresholds, formulas, rounding, minimum clamp, neutral fallbacks, and `(final_minutes, breakdown)` result remain equivalent to the former root `watering_decision.py`. The root module was removed and no compatibility copy or re-export remains.

---

## Plant Seeding

Plant seeding is manual during development.

Supported command:

```text
python -B seeding/seed_plants.py
```

The supported bulk flow:

1. loads and validates plant JSON
2. inserts all base plants
3. inserts companions and varieties after the base plants exist
4. commits the operation

Automatic startup seeding is intentionally not part of the current application initialization.

Future distributed versions may ship with pre-seeded plant data or a controlled first-run process.

---

## Weather

Current weather provider:

```text
Open-Meteo
```

Current coordinates are hardcoded to the developer’s garden location.

This is intentional for the current prototype.

Future product behavior will allow the user to select a location, after which weather requests and frost/season recommendations can use that location.

Current flows:

- app startup checks stored-weather freshness
- manual refresh is available through `/refresh_weather`
- scheduler refreshes weather using its own in-memory timing logic
- dashboard reads today’s record
- history reads recent records
- watering engine reads today’s temperature and precipitation

The app freshness check and scheduler refresh timing have different behavior and must not be unified during movement-only refactoring.

---

## Watering Engine

Inputs:

- active beds
- plant-derived watering configuration
- daily sensor slots
- weather values

Behavior:

- calculates average moisture
- skips inactive beds
- skips beds without readings
- skips incomplete watering configurations
- uses soil, temperature, and rain factors
- saves watering decisions
- logs warning events when weather is unavailable

Current output is runtime in minutes.

Future output should move toward target water volume, with runtime derived from measured flow.

`/water_now` currently logs a manual watering event and does not actuate physical hardware.

---

## Scheduler

`scheduler.py` runs as a separate process.

Current behavior:

- immediately refreshes weather after process start
- refreshes again every three days while the same process remains alive
- considers watering from 05:00 through 10:59
- runs when slot 1 exists, or after the 09:00 fallback
- runs at most once per date per scheduler process
- sleeps one hour after an engine run
- normally polls every 60 seconds
- tracks run state in memory only

These timing rules must remain unchanged during structural work.

---

## Templates and Static Files

Templates remain flat during the backend structural refactor.

All active pages use `base.html`.

Active stylesheet:

```text
static/css/main.css
```

Frontend redesign, template grouping, icons, visual garden-map work, and product design are separate future tasks.

---

## Current Structural Problems

- remaining root-level service modules are pending later Phase 3 tasks
- `plant_routes.py` is oversized and contains repeated form/JSON work
- receiver Blueprint remains at root
- no automated regression-test suite
- remaining legacy and experimental files are not yet fully organized
- some documentation still describes the pre-refactor state

These are being addressed incrementally without changing behavior.

---

## Target Structure

```text
ProjectGarden/
├── app.py
├── scheduler.py
├── requirements.txt
├── README.md
│
├── gardenhub/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── initialization.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── beds_repo.py
│   │   ├── plants_repo.py
│   │   ├── sensors_repo.py
│   │   ├── weather_repo.py
│   │   ├── watering_repo.py
│   │   └── system_events_repo.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── automation_routes.py
│   │   ├── receiver_routes.py
│   │   ├── sensor_routes.py
│   │   ├── watering_routes.py
│   │   └── plants/
│   │       ├── __init__.py
│   │       ├── catalog.py
│   │       ├── editor.py
│   │       ├── varieties.py
│   │       └── form_helpers.py
│   └── services/
│       ├── __init__.py
│       ├── calibration.py
│       ├── garden_status.py
│       ├── watering_decision.py
│       ├── watering_engine.py
│       └── weather.py
│
├── seeding/
├── plants/
├── templates/
├── static/
├── docs/
└── dev_tests/
    ├── hardware/
    ├── experiments/
    └── legacy/
```

The target is intentionally modest. It does not include an ORM, dependency injection, async architecture, frontend framework, or enterprise-style abstractions.
