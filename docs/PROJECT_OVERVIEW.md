# GardenHub Project Overview

## What GardenHub is

GardenHub is a local garden-management application for planning a garden, keeping plant knowledge in one place, using weather and sensor data, and producing explainable watering recommendations.

The project started as a personal Raspberry Pi and Arduino irrigation experiment and gradually grew into a broader garden platform.

The long-term idea is simple: GardenHub should remain useful to someone who only wants to plan and understand their garden, while also supporting sensors and automation for users who want them.

Hardware is therefore an extension of the product, not a requirement for using it.

The official product identity and logo assets are documented in [`BRAND.md`](BRAND.md).

## Current application

GardenHub currently runs as a Flask/SQLite application with a server-rendered Jinja frontend.

The main product areas are:

- Workspace
- Planner
- Garden Control
- Weather
- History
- Notifications
- Encyclopedia
- Beds and plantings
- Sensors
- Watering recommendations and records

### Planner

The Planner is a real measured 2D garden editor.

It supports garden dimensions, orientation, layers, plant placement, non-plant objects, measurement, resizing, rotation, stacking, spacing-aware plant groups and persistent saved layouts.

Planner layouts are stored in SQLite and can preserve references to beds, plantings and plants without directly modifying those domain records.

The non-plant object catalogue is still evolving. Irrigation lines and emitters currently exist as visual Planner objects only; they are not yet a hydraulic irrigation network.

### Garden Control

Garden Control uses the saved Planner layout as a read-only garden projection.

Planner bed objects that reference real GardenHub beds can be joined with current operational information such as moisture readings, sensors, watering recommendations, watering records and system events.

Other Planner objects remain visual context.

### Workspace

Workspace is the main dashboard and entry point into the application.

It combines stored garden, Weather, sensor and Planner information with clear unavailable states where a backend feature does not yet exist.

The current **Living Garden** area is a saved-layout summary rather than a rendered garden. A richer read-only garden visualization is planned for a later phase.

### Plant Encyclopedia

GardenHub includes a SQLite-backed plant knowledge system seeded from structured JSON plant sources.

The current database supports plant identity, varieties, companion relationships, spacing, calendar information, soil, nutrition, care, watering information and other growing data.

The existing Encyclopedia is functional and currently parked while a future version is designed around a “fast first, deep second” approach.

Plant editing exists, but the mutation path still needs backend work before it can safely preserve every rich field in the source plant document.

### Weather

GardenHub retrieves real Weather data from Open-Meteo.

Current and daily forecast fields are stored and used across Workspace, Weather, History and watering recommendations.

Weather is still a prototype contract in several areas. Garden location is not yet persistently owned by the backend, hourly forecasts are not implemented, and stored historical daily rows should not be treated as a reliable observation archive because they may represent forecasts retrieved earlier.

Weather is one of the next backend areas scheduled for improvement.

### Sensors

GardenHub accepts soil-moisture readings from ESP32/Arduino hardware over HTTP.

Raw values are converted to moisture percentages and stored in SQLite. These readings are used in bed summaries, Garden Control, History and watering recommendations.

Basic sensor registration and bed assignment are implemented.

Health concepts such as online/offline state, stale readings, heartbeat, battery/network status and per-sensor calibration are not yet part of the backend model.

### Watering recommendations

GardenHub calculates explainable watering recommendations using stored soil moisture together with plant moisture targets, base duration, forecast temperature and expected precipitation.

The result is stored as a recommendation with its contributing factors.

This is **not physical irrigation execution**.

Manual watering actions in the current application create watering records only. GardenHub does not currently control valves, relays, pumps or irrigation controllers, and the recommendation scheduler does not create verified watering events.

### History and notifications

History combines stored Weather, sensor readings, watering records and system events into one chronological view.

Notifications are currently a presentation layer over persisted system events. There is no separate notification lifecycle for unread, acknowledged, active or resolved state.

## Current technical shape

GardenHub intentionally uses a relatively simple stack:

- Python
- Flask
- SQLite
- Jinja templates
- CSS
- vanilla JavaScript
- Open-Meteo
- optional ESP32/Arduino soil sensors

The backend is separated into routes, services, repositories and database/schema code without introducing a heavy ORM or frontend framework.

SQLite remains appropriate for the current local single-garden application.

## Current limitations

GardenHub is still under active development.

Important current limitations include:

- single local/demo garden context rather than real multi-garden ownership;
- browser-session location preferences that do not yet configure backend Weather;
- no hydraulic irrigation model;
- no physical watering controller or actuation;
- no persisted watering schedules;
- incomplete sensor identity/health semantics;
- Weather freshness and forecast/history semantics that need improvement;
- incomplete bed/planting lifecycle management;
- plant editing that is not yet lossless;
- mixed-crop watering logic that still uses simplified aggregate thresholds.

These are tracked development areas rather than reasons to replace the current architecture.

## Direction

The next phase is focused on completing documentation and repository cleanup, followed by backend work.

Weather is the first major backend area to revisit, followed by scheduler reliability and then the remaining plant, sensor and watering issues.

Longer-term work includes:

- richer Living Garden visualization;
- persisted garden location;
- Weather current/hourly/daily modelling;
- stronger sensor health and calibration;
- safer scheduling and eventual physical irrigation control;
- hydraulic irrigation planning using real pipe lengths, diameters, flow, pressure, fittings and connected demand;
- more complete bed and planting management;
- Encyclopedia v2;
- multi-garden support.

## Development principles

GardenHub should remain understandable and practical as it grows.

The main principles are:

- reliability before complexity;
- simple and explicit Python;
- clear separation between product truth and future-facing UI;
- explainable recommendations rather than opaque automation;
- small changes that can be tested independently;
- real-world validation before unattended irrigation control;
- no architectural rewrite unless the existing structure genuinely stops serving the project.
