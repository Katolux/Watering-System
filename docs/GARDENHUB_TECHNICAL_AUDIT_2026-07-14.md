# GardenHub Technical Audit — July 2026

> Historical document. This audit was carried out on 14 July 2026 against the `v1.3-structure-review` branch. It describes GardenHub at that point in development and has since been superseded by the August 2026 frontend and backend architecture audits.
>
> It is kept as a record of the project's development, not as a description of the current application.

## Snapshot at the time

In July 2026 GardenHub was already a working local Flask/SQLite prototype with:

- HTTP sensor ingestion from Arduino/ESP32 hardware;
- Open-Meteo forecast retrieval;
- persisted sensor and weather data;
- plant data and seeding;
- explainable watering-duration recommendations;
- manual watering-event logging;
- a standalone scheduler;
- basic server-rendered management pages.

The recent structural refactor had also introduced a clearer separation between database/schema code, repositories, services and routes.

What GardenHub did **not** do at that point was physically control irrigation hardware. The scheduler created recommendations, and the manual watering path recorded events, but neither operated a valve or controller.

## Main findings

The audit considered data integrity and reliability more urgent than adding new features.

The most important issues identified were:

1. **Plant editing was lossy.** Editing a seeded plant rebuilt only the subset of JSON represented by the form, which could discard richer source data.
2. **Weather freshness was calculated incorrectly.** The latest forecast date was used as a freshness signal rather than the time the forecast had actually been retrieved.
3. **Sensor identity was not enforced.** Unknown bed and sensor IDs could submit readings.
4. **Scheduler state was only in memory.** Restarting the scheduler could repeat a run, while one early bed reading could trigger the day's only pass before other beds had reported.
5. **Manual watering input validation was weak.** Invalid references and values could reach the backend.
6. The project still lacked the safety and operational infrastructure needed for unattended physical irrigation.

Several of these findings remain useful as historical context because they helped define later backend work.

## Backend state in July

### Database

The schema covered the main prototype domains:

- zones;
- beds;
- sensors;
- plants;
- plant varieties;
- plant companions;
- bed plantings;
- sensor readings;
- weather;
- watering decisions;
- watering events;
- system events.

The main limitations were loose historical references, no general migration mechanism, limited indexing, and no persisted model for configuration, scheduler health, irrigation hardware or garden geometry.

SQLite and explicit SQL were considered appropriate for the scale of the project.

### Plant data

The plant dataset was already much richer than the UI exposed. It included watering, soil, calendar, nutrition, care, variety and companion information.

The audit found a number of dataset/index inconsistencies and, more importantly, the editing problem described above: the UI could not safely round-trip the full plant document.

### Weather

Open-Meteo retrieval, caching, retry handling and daily persistence were in place.

The main limitations were:

- hard-coded location;
- UTC assumptions;
- incorrect freshness semantics;
- no clean distinction between forecasts and observations;
- separate refresh policies between the application and scheduler.

### Sensors

The hardware-to-Flask path was working and raw values were converted to moisture percentages.

Missing pieces included:

- sensor/bed identity enforcement;
- active-state handling;
- per-sensor calibration;
- health/last-seen information;
- robust delivery/retry behaviour;
- clearer multi-sensor slot semantics.

### Watering recommendations

The watering engine combined moisture, temperature and precipitation factors to produce a recommended duration and stored the decision.

It did not model delivered water volume, flow, pressure, valves or physical execution. Mixed plantings were reduced to broad aggregate thresholds, and there were no system-wide safety limits or actuation interlocks.

### Scheduler

A standalone scheduler handled weather refresh and the morning watering-recommendation run.

Its largest weakness was that run state existed only in process memory. There was no durable run record, heartbeat or exactly-once behaviour.

## Frontend state in July

The frontend described by this audit is now historical.

At the time it was mainly a server-rendered administration interface using a shared base template and one principal stylesheet. Home was the most developed page, while Beds, Sensors, Watering, History and the plant pages were still dominated by plain forms, tables and lists.

The audit therefore recommended substantial UI work: shared cards and status components, better mobile behaviour, readable plant-detail sections, clearer watering states and more useful dashboard summaries.

Much of that frontend state changed significantly during the later 2026 frontend phase, including the Planner, Workspace, Garden Control, Weather, History, notifications and Encyclopedia presentation.

## Product capabilities that were still absent

In July, several ideas that later became important product directions had no implementation yet:

- visual garden Planner and persisted geometry;
- irrigation network planning;
- flow and pressure calculations;
- configurable garden location;
- seasonal/regional interpretation;
- hardware health monitoring;
- multi-garden ownership;
- physical multi-zone valve control.

These were correctly treated as future work rather than reasons to replace the existing Flask/SQLite architecture.

## Structural observations

The audit considered the routes/services/repositories split a positive direction and did not recommend replacing Flask or SQLite.

The main structural debt identified at the time was:

- tuple-based repository contracts;
- too much plant edit/add logic in routes;
- duplicated watering-default logic;
- configuration spread across modules;
- some unclear root-level helper scripts;
- network/database work during application import;
- little automated testing or migration support.

A lightweight typed/domain layer was suggested as a possible future improvement, but a heavy ORM or frontend framework was not considered necessary.

## Recommended priorities at the time

The July audit proposed the following reliability work before physical irrigation control:

1. make plant editing lossless;
2. repair plant-source inconsistencies;
3. tighten input and reference validation;
4. correct Weather freshness;
5. make sensor ingestion consistent;
6. make scheduler execution durable/idempotent;
7. define explicit dry-run and irrigation safety behaviour;
8. improve bed/planting management;
9. derive basic sensor health;
10. establish stronger automated tests and schema-evolution practices.

The audit explicitly advised against treating the prototype as an unattended irrigation controller until those areas were addressed.

## Historical conclusion

The main conclusion from July was that the basic architecture was worth keeping. GardenHub already had useful real functionality, but reliability and data-integrity work needed to catch up before physical actuation.

Since this audit, the application has changed substantially. In particular, the frontend and Planner described here no longer represent the current project. Refer to the current project overview, architecture documentation and later audits for the present state.
