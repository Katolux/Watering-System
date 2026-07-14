# GardenHUB Structural Refactor Plan — v1.2 to v1.3

## Objective

Reorganize the existing working GardenHUB code into a clear, professional Python package structure.

This is a structural refactor only.

The objective is to:

- move active code into logical packages
- split oversized files by responsibility
- update imports
- quarantine confirmed legacy code
- preserve all runtime behavior

The objective is not to:

- rewrite working logic
- add features
- redesign algorithms
- change SQL or schemas
- change routes or endpoints
- modify templates or frontend design
- correct unrelated plant data

---

## Core Rules

- Prefer moving code over rewriting code.
- Preserve function bodies wherever practical.
- Preserve SQL, parameter order, tuple shapes, and return values.
- Preserve route URLs, HTTP methods, Blueprint names, and endpoint names.
- Preserve template names and render contexts.
- Preserve plant JSON and manual seeding.
- Preserve weather, calibration, sensor, watering, scheduler, and Arduino behavior.
- Work in small phases.
- Verify after each phase.
- Commit each approved phase separately.
- Do not automatically continue into another phase.

---

## Approved Decisions

- Keep `app.py` as Flask constructor and owner of:
  - `/`
  - `/refresh_weather`
  - `/history`
- Do not introduce an application factory during this refactor.
- Use explicit repository filenames:
  - `beds_repo.py`
  - `plants_repo.py`
  - `sensors_repo.py`
  - `weather_repo.py`
  - `watering_repo.py`
  - `system_events_repo.py`
- Keep templates flat.
- Do not modify frontend files.
- Split `plant_routes.py` only after DB, repository, and service phases are stable.
- Preserve unused or uncertain helpers.
- Move only confirmed legacy code.
- Treat ML and external API scripts as experiments, not legacy.
- Leave Arduino and hardware diagnostics in place until separately reviewed.
- Treat plant JSON/index inconsistencies as a separate data task.
- Keep plant seeding manual.
- Supported seeding command:

  ```text
  python -B seeding/seed_plants.py
  ```

---

## Phase Status

### Phase 0 — Baseline inspection

Status: **Complete**

Completed work:

- current repository inspected
- routes and Blueprint namespaces recorded
- active, legacy, and experimental files identified
- target structure approved
- behavior-preservation requirements documented

---

### Phase 1 — Database package

Status: **Complete**

Completed moves:

- `db.py` → `gardenhub/db/connection.py`
- `db_schema.py` → `gardenhub/db/schema.py`
- `db_init.py` → `gardenhub/db/initialization.py`
- `init_weather_db()` moved into `gardenhub/db/schema.py`
- `gardenhub/db/__init__.py` created

Verification completed:

- function bodies preserved
- SQL preserved
- DB root path preserved
- initialization remained idempotent
- manual plant seeding passed
- Flask startup passed
- key pages returned HTTP 200
- route map remained unchanged

Commits:

- database package refactor
- removal of original root DB modules

---

### Phase 2 — Repository split

Status: **Complete**

#### Phase 2A — System events

Status: **Complete**

Completed move:

- `system_events_repo.py` → `gardenhub/repositories/system_events_repo.py`
- `gardenhub/repositories/__init__.py` created

Verification completed:

- 100% Git rename
- function bodies preserved
- SQL preserved
- insert/read behavior passed
- tuple shapes preserved
- Flask startup passed
- route map remained unchanged

#### Phase 2B — Weather repository

Status: **Complete**

Completed move:

- created `gardenhub/repositories/weather_repo.py`
- moved `save_weather_record()`
- moved `get_latest_weather_date()`
- moved the database-backed application `should_refresh_weather()`
- moved `get_last_days_weather()`
- moved `get_today_weather_record()`
- moved `get_today_weather()`

Preserved in their existing locations:

- Open-Meteo API request
- retry/cache configuration
- Pandas date processing
- API response formatting
- scheduler timing
- Flask routes

Verification completed:

- all six signatures and function bodies preserved
- SQL and tuple shapes preserved
- weather upsert, freshness, ordering, and missing-weather behavior passed against a disposable database
- the app and scheduler refresh checks remained separate
- Flask startup and key-page checks passed
- all 24 routes remained unchanged

#### Phase 2C — Beds repository

Status: **Complete**

Completed move:

- created `gardenhub/repositories/beds_repo.py`
- moved `add_bed()`
- moved `get_all_beds()`
- moved `assign_plant_to_bed()`
- moved `get_beds_with_plants()`
- kept the mixed `list_beds_with_sensors()` diagnostic helper in the transitional root repository because sensor metadata is outside Phase 2C
- moved confirmed legacy `historic_sensor.py` unchanged to `dev_tests/legacy/historic_sensor.py`
- added `dev_tests/legacy/README.md`

Verification completed:

- all four signatures and function bodies preserved
- SQL, parameter ordering, commits, and tuple shapes preserved
- bed creation, retrieval, plant assignment, and bed/plant aggregation passed against a disposable database
- database initialization remained idempotent
- manual three-pass plant seeding passed against a disposable database
- no active runtime imports depended on `historic_sensor.py`
- Flask startup and all required key-page checks passed
- all 24 routes remained unchanged

#### Phase 2D — Sensors repository

Status: **Complete**

Completed move:

- created `gardenhub/repositories/sensors_repo.py`
- moved `list_beds_with_sensors()`
- moved `get_all_sensors()`
- moved `add_sensor()`
- moved `assign_sensor_to_bed()`
- moved `next_slot_for_today()`
- moved `save_reading()`
- moved `get_today_moisture_slots()`
- moved `get_recent_sensor_readings()`
- kept sensor metadata and sensor-reading persistence together because they form one understandable repository at the current project size

Verification completed:

- all eight signatures and function bodies remained AST-identical
- SQL statements, parameter ordering, commit behavior, return values, and tuple shapes remained unchanged
- all active and diagnostic callers import the packaged sensor repository directly; no compatibility re-export was required
- sensor listing, assignment, recent-reading retrieval, today's moisture-slot aggregation, reading persistence, and the six-slot limit passed against a disposable database
- receiver responses remained unchanged for missing fields, invalid moisture, out-of-soil readings, accepted readings, and a seventh reading
- the packaged sensor repository imports successfully and uses the same project-root SQLite database path
- Flask startup and all required key-page checks passed
- all 24 application routes remained unchanged

#### Phase 2E — Watering repository

Status: **Complete**

Completed move:

```text
gardenhub/repositories/watering_repo.py
```

- moved `save_watering_decision()`
- moved `get_latest_watering_decision()`
- moved `log_watering_event()`
- moved `get_recent_watering_events()`
- updated the watering engine, watering routes, and automation routes to import the packaged watering repository directly
- no compatibility re-export was required

Verification completed:

- all four signatures, function bodies, SQL statements, SQL parameter ordering, transaction behavior, return values, and tuple shapes remained AST-identical
- the packaged watering repository imports successfully and uses the same project-root SQLite database path
- decision writes, latest-decision retrieval, manual event writes, and recent-event retrieval passed against a disposable database
- watering-decision tuples remained `(final_minutes, soil_factor, temp_factor, rain_factor, timestamp)`
- watering-event history tuples remained `(timestamp, bed_id, minutes, mode, source_decision_id, note)`
- watering-engine inactive-bed, missing-reading, incomplete-configuration, factor, persistence, missing-weather fallback, and system-event logging behavior passed against a disposable database
- `/water_now` remained logging-only and preserved manual mode, minutes, null factors/reference, and its note
- Flask startup and all required key-page checks passed
- all 25 application routes remained unchanged

#### Phase 2F — Plants repository

Status: **Complete**

Completed move:

- created `gardenhub/repositories/plants_repo.py`
- moved `get_all_plants_catalog()`
- moved `get_plant_by_id()`
- moved `get_plant_varieties()`
- moved `get_plant_companions()`
- moved `plant_exists()`
- moved `variety_exists()`
- moved `insert_rich_plant()`
- moved `insert_rich_variety()`
- moved `update_rich_plant()`
- moved `delete_plant()`
- moved `delete_variety()`
- updated the automation and plant route modules to import the packaged plants repository directly
- removed the root `repositories.py` after confirming that it contained no remaining active functions
- no compatibility re-export was required

Verification completed:

- all 11 function signatures and bodies remained AST-identical
- SQL, SQL parameter ordering, commits, return values, delete ordering, and JSON serialization remained unchanged
- the packaged plants repository imports successfully and uses the same project-root SQLite path
- two disposable three-pass seeding runs produced stable counts of 51 plants, 25 varieties, and 199 companion relationships
- catalog, plant, variety, and companion tuple shapes remained 7, 25, 3, and 5 fields respectively
- plant insert/update, variety insert/delete, companion cleanup, plant deletion, existence checks, and JSON-field round trips passed against a disposable database
- deletion of a plant referenced by `bed_plantings` still raises the pre-existing foreign-key `IntegrityError` and rolls back; this behavior was preserved and not corrected in this structural phase
- Flask startup and all required key-page checks passed
- all 25 application routes remained unchanged
- compilation and `git diff --check` passed
- the documented direct seeding command failed in an isolated copy unless the project root was placed on `PYTHONPATH`; the unchanged three-pass seeder passed with that path supplied, and the entry-point issue was left for a future task
- one pre-existing exploratory reference remains in `dev_tests/Main.py`: it imports the already-absent `add_bed_menu` from root `repositories`; no active runtime import references the removed module

---

### Phase 3 — Service modules

Status: **In progress**

#### Phase 3A — Calibration service

Status: **Complete**

Completed move:

- `calibration.py` → `gardenhub/services/calibration.py`
- created `gardenhub/services/__init__.py`
- updated the receiver, automation routes, and watering engine to import the packaged calibration service directly
- removed the root calibration module without a compatibility copy or re-export

Verification completed:

- the moved calibration file is byte-identical to the former root file
- constants, thresholds, function signature, function body, clamping, and integer behavior remained unchanged
- representative comparisons passed below, at, between, and above the wet/dry thresholds and at the out-of-soil threshold
- receiver missing-field, invalid-value, out-of-soil, accepted-reading, stored raw/percentage, and seventh-slot responses passed against a disposable database
- the packaged module and watering-engine imports succeeded
- Flask startup and all required key-page HTTP checks passed
- all 25 application routes remained unchanged
- compilation, stale-reference searches, duplicate-definition searches, and `git diff --check` passed

#### Phase 3B — Garden Status Service

Status: **Complete**

Completed move:

- `garden_logic.py` → `gardenhub/services/garden_status.py`
- updated the automation routes to import the packaged garden status service directly
- removed the root garden status module without a compatibility copy or re-export
- preserved the inactive `daily_average_moisture()` helper unchanged

Verification completed:

- all three function signatures and bodies remained AST-identical
- moisture thresholds, status labels, return values, calculations, display behavior, and representative edge cases remained unchanged
- the packaged garden status module imported successfully
- no Python import references the former root module
- Flask startup and the five required key-page HTTP checks passed
- all five required pages produced byte-identical rendered output before and after the move
- all 25 application routes, methods, Blueprint namespaces, and endpoint names remained unchanged
- compilation and `git diff --check` passed

#### Phase 3C — Watering Decision Service

Status: **Complete**

Completed move:

- `watering_decision.py` → `gardenhub/services/watering_decision.py`
- updated the watering engine to import the packaged watering-decision service directly
- removed the root watering-decision module without a compatibility copy or re-export

Verification completed:

- the moved source remained equivalent to the former root file apart from its final newline, and the complete module AST remained identical
- the `WateringInputs` dataclass field names, field order, types, class and function signatures, thresholds, comparison operators, formulas, rounding, minimum clamp, fallbacks, and result structure remained unchanged
- representative before/after comparisons passed for moisture below, inside, and above target; low, normal, and high temperature; no, moderate, and heavy rain; minimum clamping; the existing absence of a maximum clamp; exact boundaries; and missing moisture or weather values
- the packaged module and watering-engine imports succeeded, with no stale root import or duplicate decision/input definition
- disposable-database watering-engine checks preserved stored final minutes and soil, temperature, and rain factors for low, target-range, and high moisture
- missing-weather fallback preserved neutral factors and warning-event details without writing to the development database
- Flask startup and the five required key-page HTTP checks passed with byte-identical rendered output
- all 25 application routes, methods, Blueprint namespaces, and endpoint names remained unchanged
- compilation and `git diff --check` passed

#### Phase 3D — Weather Service

Status: **Complete**

Completed move:

- weather API orchestration → `gardenhub/services/weather.py`
- moved `refresh_weather()` with the existing Open-Meteo setup, cache/retry configuration, request parameters, response processing, Pandas date construction, record creation, repository persistence calls, and formatted console output
- updated `app.py`, `scheduler.py`, `dev_tests/Main.py`, and `dev_tests/debug_import.py` to use the packaged weather service
- removed `get_weather_new.py` without a compatibility wrapper
- preserved `historic_weather.py` unchanged as a separate repository-backed CLI history printer

Verification completed:

- the moved weather source remained equivalent to the former root file apart from its final newline, and the complete module AST remained identical
- the Open-Meteo endpoint, hardcoded coordinates, daily variables and ordering, model, timezone, cache filename and expiration, retry count and backoff, response indexes, Pandas date-range construction, conversions, record keys, float behavior, repository calls, and console output remained unchanged
- side-by-side mocked-response refreshes produced identical dates and weather values for temperature, precipitation, sunshine, daylight, wind maximum, and wind direction
- two refreshes against disposable SQLite databases preserved upsert behavior and produced three unique date rows without duplicates
- the packaged service, application, scheduler, exploratory scripts, and watering-engine repository interface imported successfully
- active weather SQL remained confined to the repository and schema layers, and the project-root SQLite path remained unchanged
- the application database-backed freshness check and scheduler in-memory three-day refresh interval remained separate
- scheduler immediate refresh, watering window, fallback behavior, and sleep durations remained unchanged
- manual `/refresh_weather` continued to call the service and redirect to `/`
- Flask startup and the four required key-page HTTP checks passed with byte-identical rendered output
- all 25 application routes, methods, Blueprint namespaces, and endpoint names remained unchanged
- compilation and `git diff --check` passed

#### Phase 3E — Watering Engine Service

Status: **Pending — next**

Next move:

- `watering_engine.py` → `gardenhub/services/watering_engine.py`

Do not begin Phase 3E without separate approval. Do not alter formulas, thresholds, fallback behavior, or scheduler logic.

---

### Phase 4 — Route organization

Status: **Pending**

Move:

- `python_receiver.py` → `gardenhub/routes/receiver_routes.py`

After DB, repositories, and services are stable, split `plant_routes.py` into:

```text
gardenhub/routes/plants/
├── __init__.py
├── catalog.py
├── editor.py
├── varieties.py
└── form_helpers.py
```

Requirements:

- one `plant` Blueprint
- identical URLs
- identical HTTP methods
- identical endpoint names
- identical templates and render contexts

---

### Phase 5 — Legacy and experiment organization

Status: **Pending**

After file-by-file approval:

- confirmed legacy → `dev_tests/legacy/`
- ML/API experiments → `dev_tests/experiments/`
- hardware diagnostics may later move to `dev_tests/hardware/`

Do not delete uncertain files.

Do not correct plant data during this phase.

---

### Phase 6 — Documentation and final cleanup

Status: **Pending**

- remove confirmed empty unused placeholders
- remove temporary compatibility re-exports
- update README repository tree
- update architecture documentation
- document supported operational commands
- perform full smoke test
- prepare merge review

---

## Behavior-Preservation Checklist

Before and after every phase, verify:

- all 24 routes retain URLs and methods
- Blueprint names remain:
  - `receiver`
  - `automation`
  - `sensor`
  - `watering`
  - `plant`
- endpoint names used by templates remain unchanged
- SQL statements remain equivalent
- table definitions and initialization order remain equivalent
- repository return tuple shapes remain unchanged
- `/sensor_data` response bodies and status codes remain unchanged
- templates and render contexts remain unchanged
- `static/css/main.css` remains active
- plant JSON remains unchanged
- seeding remains manual
- bulk three-pass seeding remains available
- watering defaults remain unchanged
- calibration remains unchanged
- moisture statuses remain unchanged
- weather behavior remains unchanged
- slot assignment remains unchanged
- watering skip conditions remain unchanged
- `/water_now` remains logging-only
- scheduler behavior remains unchanged
- Arduino behavior remains unchanged

---

## Standard Verification

```text
git diff --check
git status --short --branch
python -m compileall app.py scheduler.py gardenhub seeding
```

Also:

- search for obsolete imports
- import new modules
- start Flask
- compare route map
- load key pages
- use a disposable/development DB for approved write tests
- verify manual seeding
- confirm moved originals are removed
- stop after the requested phase

---

## Definition of Done

The structural refactor is complete when:

- database code lives under `gardenhub/db/`
- repository code is split by domain under `gardenhub/repositories/`
- active services live under `gardenhub/services/`
- active Blueprints live under `gardenhub/routes/`
- `repositories.py` is removed
- root-level active modules are reduced to intentional entrypoints and hardware/operational files
- templates remain functional
- all routes and behavior remain unchanged
- legacy and experiments are clearly separated
- documentation matches the real repository
- the branch passes final local smoke testing
