# GardenHub Architecture

## Overview

GardenHub is a local Flask/SQLite garden-management application.

The backend is intentionally simple: Flask routes and Blueprints handle HTTP requests, services contain application/domain logic, repositories own SQLite access, and Jinja templates render the server-side interface. Vanilla JavaScript is used where the frontend needs richer interaction, most notably in the Planner.

The application currently supports several real but separate domains:

- garden planning and saved Planner layouts;
- plant knowledge and plantings;
- soil-moisture sensors and readings;
- Weather retrieval and storage;
- watering recommendations and manual watering records;
- Garden Control projection;
- History;
- system-event-backed notifications.

GardenHub does **not** currently control irrigation hardware. Watering decisions are recommendations, and manual watering actions are records of watering rather than commands to valves or pumps.

## Runtime shape

```text
Browser
  |
  v
Flask routes / Blueprints
  |
  +--> services / presentation logic
  |      |
  |      +--> repositories --> SQLite
  |
  +--> Jinja templates
  |
  +--> JSON endpoints used by Planner

ESP32 / Arduino
  |
  | POST /sensor_data
  v
sensor receiver
  |
  v
calibration + sensor repository
  |
  v
SQLite

scheduler.py
  |
  +--> Weather refresh
  |
  +--> watering recommendation engine
          |
          +--> watering_decisions
          +--> system_events
```

The scheduler is a separate process from Flask.

## Main layers

### Routes and Blueprints

HTTP handling lives under `gardenhub/routes/` together with the plant-route package.

Routes should mainly deal with:

- request parsing;
- basic validation;
- calling the relevant service or repository;
- choosing a response, redirect or template.

Some older routes still contain more domain/presentation work than this ideal, but the general structure is already in place.

The application currently registers Blueprints for the main functional areas, including sensor ingestion, automation/Garden Control, sensors, watering, plants, Weather, Planner and notifications.

`app.py` remains the Flask application entry point and also owns a small number of top-level pages such as Workspace and History.

No application-factory rewrite is currently needed.

### Services

Services sit between routes and repositories when a feature needs orchestration or domain logic.

Important service areas currently include:

- soil-moisture calibration;
- garden/bed status;
- watering-decision calculations;
- watering-engine orchestration;
- Weather retrieval and transformation;
- Workspace/overview composition;
- garden context;
- Planner layout validation/presentation;
- Planner-to-Garden-Control projection;
- History aggregation;
- plant Encyclopedia presentation;
- notification presentation.

Not every read path needs a service. Small repository queries can remain direct where the extra layer would not improve clarity.

### Repositories

Repositories own SQLite queries and persistence.

Current repository domains include:

- beds and plantings;
- plants, varieties and companions;
- sensors and sensor readings;
- Weather;
- watering decisions and watering events;
- system events;
- Planner layouts.

The project uses explicit SQL rather than an ORM. That remains a reasonable choice for the current local application.

### Database

SQLite is the runtime data store.

The current schema contains 13 main tables:

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
- `planner_layouts`

Foreign-key enforcement is enabled on database connections, although some historical/event relationships are intentionally loose and a few integrity gaps remain.

GardenHub currently has no general migration framework. Schema evolution is still handled through initialization/create-if-absent logic and targeted additions. That is acceptable for the prototype but is known technical debt.

## Planner architecture

The Planner is the most client-heavy part of GardenHub.

### Frontend ownership

The browser owns interactive editing behaviour such as:

- drag and drop;
- pan and zoom;
- measurement;
- resize and rotation;
- stacking;
- layer visibility;
- plant spacing/footprint calculation;
- plant-group quantity calculation;
- temporary selection state.

The Planner keeps its internal geometry in metric units.

### Persistence

Saved Planner layouts are stored in `planner_layouts`.

A layout contains the garden-level metadata and an ordered collection of objects. The backend validates the shape, supported object/layer combinations, dimensions, IDs, rotation, quantities and geometry bounds before saving.

Planner persistence is currently a whole-document save. It is effectively last-write-wins and has no revision history.

### Domain references

Planner objects may preserve identifiers such as:

- `plantId`;
- `bedId`;
- `sourcePlantingId`;
- zone labels/references.

These references are metadata links, not mutations.

Saving a Planner layout does not create, update or delete beds, plantings or plants. Missing or stale references are deliberately preserved rather than silently deleting Planner objects.

This separation is important: Planner geometry and operational garden data are related, but they are not the same source of truth.

### Object catalogue

Plant information used by Planner comes from the SQLite plant catalogue.

Most non-plant Planner object families are currently defined by the frontend catalogue rather than by dedicated backend domain tables.

Irrigation lines and emitters are therefore saved as normal measured Planner objects. They are **not** currently a connected irrigation network.

A future expansion of the object catalogue should move toward one central object/component definition source so metadata is not duplicated across template, JavaScript, CSS and backend validation.

## Garden Control

Garden Control is a read-only operational projection of the saved Planner layout.

The backend reads the saved layout and converts its geometry into percentages for responsive display. It does not rewrite the Planner geometry.

When a saved Planner bed object contains a `bedId` that matches a current domain bed, Garden Control can attach operational information such as:

- bed state;
- plant names;
- zone;
- latest moisture;
- configured sensors;
- latest watering recommendation;
- latest watering record;
- relevant warning/error events.

Unlinked beds and non-bed objects remain visual context.

Garden Control is not a second editor and should not become one. Planner owns geometry editing; Garden Control owns operational presentation.

## Workspace

Workspace is composed from several read models rather than from a dedicated dashboard database.

Its inputs include garden/domain summaries, Weather information and saved Planner state.

The current Living Garden surface only knows whether a layout exists and can summarize its garden metadata and object counts. It does not render the saved Planner objects.

A future Living Garden renderer should derive from the saved Planner geometry rather than introduce a second independent garden layout.

## Plant system

Structured JSON files under `plants/` are the seed source for plant knowledge.

At runtime, SQLite is the application record store.

The plant domain includes:

- plant definitions;
- varieties;
- companion relationships;
- spacing and calendar data;
- soil, nutrition and care information;
- watering-related derived fields.

Planner and the Encyclopedia read plant information from the runtime database rather than directly from JSON files.

Web editing currently updates SQLite only. It does not rewrite the JSON seed sources.

The current edit path can replace rich `plant_json` with a reduced document, so plant mutation remains an area requiring backend correction before it should be considered fully reliable.

## Beds, plantings and zones

Beds are domain records separate from Planner objects.

A bed can contain multiple planting rows. A planting can hold a plant reference, optional variety reference, quantity, planted/removed dates, notes and override fields.

The current frontend exposes only part of this lifecycle.

Zones currently provide basic grouping through an ID/name/active record. They are not yet hydraulic irrigation zones and do not represent valve state.

## Sensor ingestion

The active sensor receiver accepts HTTP posts from ESP32/Arduino nodes.

Current payload fields are based on:

- bed ID;
- sensor ID;
- raw moisture.

The receiver converts accepted raw values through the current calibration and persists both raw and percentage values.

Sensor readings are currently organised into six daily slots at bed level.

Known limitations include:

- sensor/bed identity is not strictly enforced during ingestion;
- configured active state is not a reliable online/offline signal;
- calibration is global rather than per sensor;
- there is no heartbeat, last-seen, stale-state, battery or network-health model;
- multi-sensor slot semantics need improvement.

These are backend reliability issues, not reasons to replace the ingestion architecture.

## Weather

Open-Meteo is the current Weather provider.

GardenHub retrieves real current and daily forecast data and stores it in SQLite. Weather is consumed by:

- the global application header;
- Workspace;
- the Weather page;
- History;
- watering recommendations;
- the scheduler.

The current Weather model is intentionally temporary.

Important limitations are:

- backend coordinates still come from a fixed fallback garden context;
- browser-selected location is session-only and does not configure backend retrieval;
- hourly Weather is not yet implemented;
- current and daily data share the existing storage approach;
- stored past daily rows may represent forecasts rather than verified observations;
- freshness currently relies on forecast dates rather than a trustworthy last-successful-retrieval timestamp;
- timezone ownership is not fully consistent.

Weather is the first major backend area planned for the next development phase.

## Watering recommendations

`watering_decision` contains the deterministic calculation.

The current inputs include:

- average soil moisture;
- plant-derived minimum/maximum moisture;
- plant-derived base duration;
- daily maximum temperature;
- expected precipitation.

The result is a recommended duration plus the factor breakdown used to reach it.

`watering_engine` orchestrates those calculations across beds and persists the resulting `watering_decisions`.

The current engine:

- skips inactive beds;
- skips beds without usable readings;
- skips incomplete watering configuration;
- uses neutral Weather factors when Weather is unavailable;
- records warning events where appropriate.

Multiple plantings are currently collapsed into aggregate watering values. That behaviour needs a deliberate mixed-crop design rather than an accidental formula change.

## Watering events

`watering_events` are records of watering.

The current `/water_now` path creates a manual record. It does not send a command to physical hardware.

There is currently no:

- relay or valve service;
- controller state;
- flow measurement;
- delivered-volume confirmation;
- automatic event creation from recommendations;
- persisted watering schedule.

Any later actuation layer should remain separate from recommendation calculation so the system can distinguish **recommended**, **commanded** and **actually delivered** water.

## Scheduler

`scheduler.py` runs independently from the Flask process.

Its current responsibilities are:

- periodic Weather refresh;
- running the watering recommendation engine during the morning window.

The scheduler is a recommendation scheduler, not an irrigation controller.

Current run state is held in process memory, which creates known reliability problems:

- restart can lose the once-per-day guard;
- an early reading from one bed can trigger the day's single run before later beds report;
- recommendation runs are not durably idempotent.

Scheduler behaviour will be revisited after the Weather backend is corrected.

## History and notifications

History is a read-only aggregation rather than a dedicated unified event table.

It currently combines:

- stored daily Weather/forecast records;
- sensor readings;
- watering events;
- system events.

Notifications are another presentation over `system_events`.

There is no separate notification entity or lifecycle for unread, acknowledged, active or resolved state.

Future history work can add more domain events and correlations without requiring the existing tables to be replaced immediately.

## Garden context

GardenHub currently behaves as a single local garden, with a deterministic demo-garden mode for demonstrations/testing.

The Planner layout uses a garden identifier, but operational tables such as beds, sensors, Weather, watering and events do not currently carry persisted garden ownership.

The browser can also hold a temporary garden/location preference, but this is presentation/session state rather than a backend multi-garden model.

Real multi-garden support would require ownership to be introduced consistently across the operational domains.

## Frontend structure

The application uses:

- Jinja templates;
- shared shell/header/sidebar components;
- CSS;
- vanilla JavaScript.

Most screens remain server-rendered.

The Planner is intentionally more JavaScript-heavy because direct manipulation, geometry and canvas-like interaction are client concerns.

There is currently no reason to introduce React or another frontend framework solely for architectural fashion. The existing approach is appropriate while the client-side modules remain understandable and testable.

## Hardware boundary

The current physical integration stops at soil-moisture ingestion.

ESP32/Arduino firmware can submit readings to GardenHub, but the application has no controller/valve/relay/flow contract.

Future hardware work may add:

- registered device identity;
- stronger delivery/retry behaviour;
- per-sensor calibration and health;
- controller/valve abstraction;
- acknowledgements;
- flow feedback;
- safety state;
- fail-safe behaviour.

Physical actuation should only be introduced after the recommendation, scheduling and safety layers are reliable.

## Known architectural debt

The current architecture is sound for the prototype, but several issues remain:

- no general migration system;
- some routes/services still use positional repository tuples;
- some presentation/domain ownership remains mixed;
- application startup can still cause database/network side effects;
- scheduler state is not durable;
- Weather freshness/location semantics need correction;
- sensor ingestion identity rules need correction;
- plant mutation is not lossless;
- some event/history relationships are deliberately weak;
- the project is still single-garden;
- testing is not yet as isolated or comprehensive as it should be.

None of these currently justify an ORM, microservices, dependency injection or a wholesale application rewrite.

## Architectural direction

The preferred direction is incremental:

1. keep Flask and SQLite;
2. keep explicit routes, services and repositories;
3. strengthen domain contracts where current tuple/JSON boundaries are fragile;
4. fix Weather and scheduler reliability;
5. correct plant and sensor integrity issues;
6. add domain models only where a real feature requires them;
7. design irrigation hydraulics as a separate connected domain before implementing it;
8. introduce physical actuation only behind clear safety and execution boundaries;
9. add multi-garden ownership only when that product phase begins.

The architecture should grow in response to real GardenHub requirements rather than being made more complicated in anticipation of them.
