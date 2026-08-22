# GardenHub Architectural Decisions

This file records architectural choices that are still useful to remember.

Older refactor-only decisions have either been folded into the current architecture or marked as historical so they are not mistaken for active restrictions.

## ADR-001 — Keep the current Flask application structure

**Status:** Accepted

GardenHub keeps `app.py` as the current Flask application entry point.

There is no present need to introduce a full application factory.

The existing structure is understandable and appropriate for the current local application. An application factory can be reconsidered later if testing, configuration or deployment requirements make it genuinely useful.

## ADR-002 — Keep the backend simple and explicit

**Status:** Accepted

GardenHub should prefer:

- Flask Blueprints and ordinary functions;
- explicit services where orchestration/domain logic is useful;
- explicit repository modules;
- parameterized SQL;
- SQLite for the current local application.

Do not introduce an ORM, dependency-injection framework, microservices, async architecture or other large abstraction simply because it is considered more advanced.

Architecture should become more complex only when a real GardenHub requirement justifies it.

## ADR-003 — Use domain-specific repositories

**Status:** Accepted

Database access is grouped into explicit domain repositories such as:

- beds/plantings;
- plants/varieties/companions;
- sensors/readings;
- Weather;
- watering;
- system events;
- Planner layouts.

This is preferred over a generic repository framework because it keeps ownership easy to follow.

## ADR-004 — Keep product assets and frontend folders outside the Python package

**Status:** Accepted

Folders such as:

- `plants/`
- `seeding/`
- `templates/`
- `static/`
- `docs/`
- `dev_tests/`

remain top-level project folders.

They do not need to live inside `gardenhub/` merely for structural consistency.

## ADR-005 — Plant source data and runtime data have different roles

**Status:** Accepted

Structured JSON files under `plants/` are the seed/source dataset.

SQLite is the active runtime record store.

Plant seeding remains an explicit development/data-management action rather than something Flask should silently perform on every startup.

Web edits currently affect SQLite only and do not rewrite the source JSON files.

This boundary must stay clear, especially while plant editing and reseeding behaviour are improved.

## ADR-006 — Planner geometry is separate from garden domain truth

**Status:** Accepted

The Planner owns editable garden geometry and stores it as a persisted layout.

Beds, plantings, plants, sensors and other operational records remain separate domain data.

Planner objects may keep references such as `bedId`, `plantId` and `sourcePlantingId`, but saving a layout must not silently create, modify or delete those domain records.

Garden Control may project operational information onto matching Planner objects, but it remains read-only.

This separation allows the garden drawing to evolve without turning Planner saves into hidden database mutations.

## ADR-007 — Garden Control is a projection, not a second editor

**Status:** Accepted

Planner is the geometry editor.

Garden Control displays the saved Planner layout read-only and adds operational state where matching domain references exist.

Editing geometry from Garden Control would create two competing layout owners and should not be added without deliberately revisiting this decision.

## ADR-008 — Irrigation Planner and watering execution are separate domains

**Status:** Accepted

Current Planner irrigation lines and emitters are visual/measured objects only.

A future hydraulic irrigation system must be designed as a real connected domain with concepts such as:

- pipe segments and components;
- tubing type/diameter;
- connectivity;
- flow;
- pressure;
- friction loss;
- emitters;
- zones;
- source capacity;
- demand;
- warnings.

Likewise, watering recommendations must remain distinct from physical execution.

A future automation system should distinguish:

1. recommended watering;
2. commanded watering;
3. confirmed delivered watering.

Physical actuation should not be added by simply extending the current recommendation record.

## ADR-009 — Single-garden remains the current backend contract

**Status:** Accepted for current phase

GardenHub currently operates as one local garden plus a deterministic demo context.

Frontend garden/location selectors must not be mistaken for real multi-garden backend ownership.

When multi-garden support is introduced, ownership must be added consistently across beds, plantings, sensors, Weather, watering, events and Planner layouts.

Do not build partial multi-garden behaviour only in the UI.

## ADR-010 — Weather location belongs to garden/domain configuration

**Status:** Direction accepted; implementation pending

Backend Weather currently uses a temporary fallback location.

The future location model should be persisted as garden configuration and should drive server-side Weather retrieval and later frost/seasonal logic.

Browser-session geolocation is useful for presentation/prototyping but is not the final source of truth.

## ADR-011 — Keep legacy, experiments and hardware diagnostics distinct

**Status:** Accepted

Historical/broken reference code belongs under `dev_tests/legacy/`.

Experimental work belongs under `dev_tests/experiments/`.

Manual hardware/network diagnostics belong under `dev_tests/hardware/`.

Primary firmware and its safe configuration template may remain separate from those diagnostics.

The purpose is not merely tidiness: experimental or diagnostic code should never be mistaken for a supported runtime contract.

## ADR-012 — Prefer small, reviewable changes

**Status:** Accepted

Structural, functional, data and visual changes should normally be kept separate when practical.

This makes regressions easier to identify, Git history easier to understand and backend learning easier to follow.

Large rewrites should be avoided unless the current architecture genuinely blocks progress.

---

# Historical decisions

The following decisions were important during the v1.2 → v1.3 structural refactor but are no longer active project constraints:

- the structural refactor had to preserve behaviour exactly;
- templates had to remain untouched during that refactor;
- Weather coordinates had to remain hardcoded during that refactor;
- plant-data inconsistencies had to be left untouched during that refactor;
- Codex work was divided into narrowly isolated structural phases.

Those rules served their purpose: they allowed the package/repository/service/route reorganization to be reviewed without mixing it with functional changes.

The structural refactor is complete, so these should now be treated as development history rather than instructions for future GardenHub work.
