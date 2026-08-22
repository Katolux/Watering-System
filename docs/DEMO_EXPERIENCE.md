# GardenHub Demo Experience

## Purpose

GardenHub includes a deterministic demo mode for showing and testing the application without using the real local garden database.

The demo is useful for:

- frontend development;
- visual regression checks;
- demonstrations;
- testing pages that need representative sensor, Weather, watering and event data;
- checking empty/non-empty operational states without modifying a real garden.

Demo data should never be treated as real garden history or as evidence that hardware or physical watering occurred.

## Demo database

The demo uses an isolated SQLite database:

```text
dev_data/gardenhub_demo.db
```

Database selection remains centralized in `gardenhub/db/connection.py`.

`GARDENHUB_DB_PATH` can select an explicit database. Without that override, GardenHub uses the normal local database.

The demo commands set the database path before importing the application or repositories so demo activity remains isolated from the real local garden.

## Commands

```powershell
python -m gardenhub.seeding.demo reset
python -m gardenhub.seeding.demo seed
python -m gardenhub.seeding.demo serve
```

### `reset`

Recreates the approved demo database from a clean state and loads the deterministic demo dataset.

### `seed`

Rebuilds the demo records so the main seeded dataset can be reproduced consistently.

### `serve`

Runs GardenHub against the demo database.

Normal startup remains:

```powershell
python app.py
```

and does not automatically switch to or seed the demo database.

## Demo identification

When GardenHub is connected to the demo database, the application displays a persistent **Demo data** indicator.

Demo Weather, sensor readings, watering records, decisions and system events should always be presented as stored demonstration data rather than as live hardware state.

## Seeded dataset

The current deterministic demo dataset includes:

| Record | Count |
| --- | ---: |
| Plants | 52 |
| Varieties | 25 |
| Companion relationships | 205 |
| Zones | 3 |
| Beds | 6 |
| Plant assignments | 9 |
| Moisture sensors | 6 |
| Moisture readings | 100 |
| Watering decisions | 10 |
| Watering events | 12 |
| Weather records | 14 |
| System events | 12 |

The six demo sensors include both configured-active and configured-inactive examples.

The plant catalogue is built from the same plant seed sources used by the normal application; demo mode does not invent a separate plant catalogue.

These counts describe the current deterministic seed contract and may change intentionally as the demo evolves.

## What the demo represents

### Workspace

Workspace shows a representative garden using stored demo beds, plantings, sensors, Weather, watering information and system events.

The current Living Garden area remains a saved-layout summary rather than a full rendered garden.

Unavailable product areas should remain visibly unavailable rather than being simulated merely for the demo.

### Planner

The demo can be used with the real Planner frontend and Planner persistence contract.

Planner geometry, objects, layers, orientation, plant groups, measurement and saved layouts are real application behaviour.

Demo Planner data should remain isolated from the local garden.

One current cleanup issue is that demo reseeding does not yet provide a perfect lifecycle guarantee for every existing `planner_layouts` row. When validating a completely clean Planner state, confirm the demo layout state explicitly rather than assuming all previous Planner layouts were removed by the seed command.

### Garden Control

Garden Control uses the saved Planner layout in the same read-only way as the normal application.

Bed objects whose `bedId` matches seeded demo beds can display operational demo information. Other Planner objects remain visual context.

The demo does not simulate controller state, valves, flow or physical watering.

### Weather

The demo contains stored Weather records so the Weather page, Workspace and History can render consistently without depending on a live provider call.

These rows are demonstration data.

Live refresh is restricted in demo mode where appropriate, and the demo should not imply that browser location controls backend Weather.

### Sensors

Demo sensors and readings provide representative active/inactive configuration and moisture histories.

Configured inactive sensors should not be described as genuinely offline; GardenHub does not yet have a connectivity/heartbeat model.

### Watering

The demo contains stored watering recommendations and manual watering records.

Recommendations are calculations. Watering events are records.

Neither represents real valve actuation or verified water delivery.

### History and notifications

The demo provides Weather, sensor, watering and system-event records so the combined History and notification presentations have useful content.

Notifications remain a presentation over `system_events`; unread/read and active/resolved state are not simulated.

### Encyclopedia

The demo uses the normal seeded plant catalogue, including varieties and companion relationships.

Encyclopedia content remains general plant knowledge rather than a claim that a particular plant is currently growing in the demo garden unless a separate planting record says so.

## Demo garden context

Demo presentation metadata is kept separately from the main operational tables.

The demo currently represents one garden context rather than a true multi-garden system.

Its garden name/dimensions/context are presentation/test data and should not be mistaken for a production `gardens` domain model.

## What should not be faked

The demo should remain honest about capabilities that GardenHub does not yet have.

Do not fabricate:

- physical irrigation execution;
- controller/relay/valve state;
- flow or pressure telemetry;
- genuine sensor online/offline state;
- notification acknowledgement/resolution state;
- persisted watering schedules;
- hydraulic irrigation calculations;
- multi-garden ownership;
- a completed Living Garden renderer;
- Weather observations where the system only has stored forecast/demo data.

A useful demo should exercise real GardenHub contracts with representative data, not make future features appear implemented.

## Visual/browser verification

The main browser smoke check is:

```text
dev_tests/frontend_shell_visual_check.cjs
```

It is used to exercise the current shared shell and important pages across desktop, tablet and mobile layouts, including interaction and overflow checks.

Other focused smoke scripts may be used for Planner persistence and related frontend contracts.

After browser testing, stop any local demo/Flask processes that were started for the check so an old server does not remain on port `5000`.

## Current demo boundary

Demo mode is a development and presentation tool.

It should remain:

- isolated from the real garden database;
- deterministic enough for repeatable frontend checks;
- representative of real application contracts;
- clearly labelled;
- conservative about capabilities that are still future work.

It is not a second product mode with different business logic, and it should not become one.
