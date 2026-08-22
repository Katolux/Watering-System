# GardenHub Roadmap

## Current position

GardenHub has moved well beyond the early irrigation-prototype stage.

The current application already includes a working Planner, saved garden layouts, Garden Control, a plant Encyclopedia, Weather, sensor ingestion, watering recommendations, History, notifications, and a much more complete frontend.

The immediate goal is not to add another large feature. It is to finish documenting the current system accurately, push the real work-in-progress state to GitHub, then return to backend development in a controlled order.

## Current phase — Documentation and repository cleanup

Before backend development resumes:

- finish the current documentation pass;
- remove or archive stale documentation;
- review `.gitignore`;
- keep private/internal development material out of the public repository;
- review generated/demo/test artifacts;
- confirm no secrets, disposable databases, logs or caches are being committed accidentally;
- run final smoke/status checks;
- push the current project state to GitHub.

Known limitations should remain visible. The repository does not need to look “finished”; it needs to be accurate.

---

# Backend roadmap

## 1. Weather

Weather is the first backend area to revisit.

Current issues:

- freshness is based on forecast horizon rather than last successful retrieval;
- backend location still uses a fixed fallback;
- browser location does not affect server-side Weather;
- current and daily data share the existing storage model;
- hourly Weather is not implemented;
- past stored daily rows may be forecasts rather than observations;
- timezone ownership is inconsistent between provider, persistence and scheduler.

### Weather v2 direction

The next Weather model should support:

- persisted garden location;
- current Weather;
- hourly 24–48 hour forecast;
- daily forecast;
- clear forecast-versus-observation semantics;
- reliable retrieval/freshness metadata;
- ET0 and other irrigation-relevant values.

The existing daily model does not need to be thrown away blindly. The data contract should be redesigned first, then implemented in small steps.

---

## 2. Scheduler reliability

Once Weather retrieval and freshness are reliable, review the scheduler.

Current problems include:

- run state stored only in process memory;
- restart can repeat a daily recommendation run;
- one bed can trigger the only run before other beds report;
- no durable per-bed/date idempotency;
- Weather refresh and watering-run timing follow separate rules;
- no first-class heartbeat/run record.

The immediate target is a reliable **recommendation scheduler**, not physical irrigation control.

---

## 3. Plant and Encyclopedia backend integrity

The Encyclopedia UI can remain parked while the backend mutation contract is corrected.

Important work:

- make plant editing lossless;
- define ownership between JSON seed sources and SQLite runtime records;
- keep rich `plant_json` and relational data consistent;
- make variety creation/resolution consistent;
- protect variety references in existing plantings;
- clarify plant deletion versus retained planting history.

Encyclopedia v2 remains a later product phase.

---

## 4. Sensor integrity and health

The sensor ingestion path already works, but identity and state semantics need improvement.

Near-term work:

- validate sensor identity;
- verify claimed bed assignment;
- respect configured sensor/bed active state;
- define correct multi-sensor slot behaviour;
- tighten raw-value handling.

Later sensor work:

- per-sensor calibration;
- last-seen timestamps;
- stale/missing-reading states;
- heartbeat/device health;
- battery/network/firmware telemetry where useful;
- stronger delivery/retry behaviour in firmware.

“Configured active” should remain distinct from “online”.

---

## 5. Beds, plantings and zones

The backend already stores more planting information than the current management UI exposes.

Future work includes:

- individual planting management;
- quantity display/editing;
- variety selection;
- planted date and notes;
- remove/soft-remove planting;
- bed active-state changes;
- safe bed deletion;
- moving beds between zones;
- zone creation/editing.

Current `zones` are organizational records only. Hydraulic irrigation-zone meaning belongs to the irrigation-planning phase.

---

## 6. Watering model

The current deterministic recommendation model should remain understandable and explainable.

Near-term work:

- improve backend validation for manual watering records;
- make scheduler/engine execution idempotent per bed/date;
- isolate failures per bed;
- clarify recommendation/event relationships.

### Mixed plantings

Current watering configuration combines multiple active plantings into broad aggregate values.

That is a known simplification.

Before changing it, define the actual domain rules for:

- main crop versus companion plants;
- quantities;
- varieties;
- growth stage;
- root depth;
- sensor depth;
- soil profile;
- irrigation sensitivity.

The calculation should be designed intentionally rather than patched incrementally.

---

## 7. History and notifications

History currently combines:

- stored Weather/forecast rows;
- sensor readings;
- watering records;
- system events.

Possible later additions:

- watering decisions as timeline entries;
- planting changes;
- Planner saves/changes;
- bed/sensor configuration changes;
- rain/watering effects;
- cross-domain correlation views.

Notifications currently reuse `system_events`.

A dedicated notification lifecycle should only be introduced if the product needs unread/read, acknowledgement, active/resolved state or delivery channels.

---

# Planner and product roadmap

## Living Garden

Workspace currently shows a saved-layout summary, not a rendered garden.

The future Living Garden should:

- derive from the saved Planner layout;
- remain read-only;
- preserve exact Planner geometry;
- potentially become richer or 3D;
- eventually respond to season, planting state and garden history.

It should not become a second independent layout editor.

---

## Advanced irrigation Planner

The current Planner already stores measured irrigation lines and emitters as visual objects.

The future irrigation system is a separate domain.

Planned concepts include:

- irrigation-planning mode;
- connected network nodes and segments;
- tubing type and internal diameter;
- physical pipe length derived from Planner scale;
- bucket-test flow input;
- source pressure/flow;
- friction-loss calculations;
- emitters and emitter flow;
- valves, T-junctions, elbows, couplers, filters and regulators;
- hydraulic zones;
- connected demand;
- runtime/volume calculations;
- layout-derived shopping quantities;
- warnings for insufficient flow/pressure or unsuitable runs.

Before this work expands, the Planner should move toward a central object/component registry so catalogue metadata is not duplicated across frontend and backend files.

Hydraulic formulas and the underlying data model should be designed before implementation.

---

## Physical irrigation control

Physical actuation remains a later phase.

It may eventually include:

- controller abstraction;
- relays/valves;
- acknowledgements;
- flow feedback;
- verified delivered volume;
- schedules;
- controller state;
- fail-safe behaviour;
- panic stop;
- hard watering limits.

A future system should clearly distinguish:

1. recommended watering;
2. commanded watering;
3. confirmed delivered watering.

Live unattended control should only come after the recommendation, scheduler, sensor-health and safety layers are reliable.

---

## Encyclopedia v2

The current Encyclopedia v1 remains usable and parked.

The future design follows the **Fast first, deep second** principle.

The first view should answer common questions quickly:

- Can I grow this here?
- When do I sow/transplant?
- How much space does it need?
- Sun or shade?
- When can I harvest?
- What grows well beside it?

Deeper sections can then cover growing technique, care/problems, harvest/use, varieties and personal garden history.

---

## Multi-garden

GardenHub currently has a single local/demo garden context.

Real multi-garden support is deliberately deferred.

When implemented, garden ownership must be introduced consistently across:

- beds;
- plantings;
- sensors;
- Weather;
- watering decisions/events;
- system events;
- Planner layouts;
- location/configuration.

It should not be simulated only in the frontend.

---

# Reliability and operations

Operational improvements remain important before real hardware control.

Future work includes:

- dependable `systemd` services for Flask and scheduler;
- automatic SQLite backups;
- restore procedure;
- process health/heartbeat;
- structured logs where useful;
- clearer startup/shutdown procedure;
- improved test isolation;
- schema migration/versioning strategy.

These do not all need to happen before normal backend development, but they become increasingly important before GardenHub is trusted to operate unattended.

---

# Longer-term possibilities

Not current priorities:

- seasonal crop planning;
- crop rotation assistance;
- frost/region-based recommendations;
- multi-language UI;
- appearance preferences;
- richer export/reporting;
- hardware OTA/configuration improvements;
- cloud or SaaS deployment;
- premium planning/analysis features;
- AI-assisted observations based on a user's own historical garden data.

These should only be developed when the underlying GardenHub data is good enough to make them useful.

---

# Current priority order

1. Finish documentation.
2. Clean repository/Git state.
3. Push the current work-in-progress version.
4. Rework Weather.
5. Make Weather scheduling reliable.
6. Fix scheduler per-bed/date recommendation behaviour.
7. Correct plant mutation/integrity issues.
8. Harden sensor ingestion and identity.
9. Complete more of the beds/plantings lifecycle.
10. Revisit mixed-crop watering logic.
11. Improve operational reliability and testing as needed.
12. Design the irrigation data model and calculations before building the hydraulic system.
13. Return to larger future features such as Living Garden, Encyclopedia v2, multi-garden and physical automation when their phase begins.

This file replaces the older `NEXT_STEPS.md`. Short-term next actions and longer-term direction should now stay together here so the project has one maintained roadmap rather than two documents that drift apart.
