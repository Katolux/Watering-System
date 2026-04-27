# Backend Restructure Plan (v1.2 → v1.3)

## Goal

Move from:
- monolithic `app.py`
- mixed responsibilities (routes + logic + DB)

To:
- modular structure
- clear separation of concerns
- maintainable codebase

---

## Current Problems

- `app.py` > 1000 lines
- routes, logic, DB mixed together
- difficult to debug and extend
- risk of breaking things when adding features

---

## Target Structure

ProjectGarden/
│
├── app.py                  # small entry point only
├── config.py
├── requirements.txt
├── README.md
│
├── gardenhub/
│   ├── __init__.py         # create_app()
│   ├── routes/
│   │   ├── main_routes.py
│   │   ├── automation_routes.py
│   │   ├── plant_routes.py
│   │   ├── sensor_routes.py
│   │   └── watering_routes.py
│   │
│   ├── repositories/
│   │   ├── beds_repo.py
│   │   ├── plants_repo.py
│   │   ├── sensors_repo.py
│   │   ├── watering_repo.py
│   │   └── system_events_repo.py
│   │
│   ├── services/
│   │   ├── watering_engine.py
│   │   ├── watering_decision.py
│   │   ├── weather_service.py
│   │   └── calibration.py
│   │
│   └── db/
│       ├── connection.py
│       ├── schema.py
│       └── init.py
│
├── templates/
│   ├── base.html
│   ├── automation/
│   ├── plants/
│   ├── sensors/
│   └── watering/
│
├── static/
│   └── css/
│       └── main.css
│
├── plants/
├── seeding/
├── docs/
└── dev_tests/

---

## Refactor Strategy

Refactoring is performed incrementally to ensure system stability.

The application must remain runnable at all times during the process.

Each step follows the cycle:
- implement change
- test functionality
- commit changes

Feature development is paused during refactoring.

---

## Phase 1 – Route Extraction

**Objective**

Reduce the size and responsibility of `app.py` without changing behavior.

**Actions**

- Create `gardenhub/routes/`
- Move route definitions into:
  - `automation_routes.py`
  - `plant_routes.py`
  - `sensor_routes.py`
  - `watering_routes.py`
- Introduce Flask Blueprints
- Register Blueprints in `app.py`

**Result**

- Reduced complexity in `app.py`
- No functional changes

---

## Phase 2 – Separate Logic from Routes

**Objective**

Ensure routes only handle HTTP concerns.

**Actions**

Move business logic into `services/`:
- watering engine
- watering decision logic
- weather handling
- calibration

Routes should:
- receive request
- call service layer
- return response

---

## Phase 3 – Repository Cleanup

**Objective**

Establish a clean and predictable database layer.

**Rules**

- SQL is only written inside repositories
- No business logic inside repositories
- Consistent return structures

---

## Phase 4 – Template Organization

**Actions**

Restructure templates:
templates/
automation/
plants/
sensors/
watering/


Fix:
- broken links
- inconsistent naming

---

## Phase 5 – Static & CSS

**Actions**

Create:
static/css/main.css


Start with:
- spacing
- typography
- table readability

No frameworks required.

---

## Phase 6 – Final Cleanup

- remove unused code
- remove debug statements
- unify naming conventions
- eliminate duplicate logic

---

## Rules During Refactor

- Small, incremental changes only
- Test after each step
- Commit frequently
- No feature development during refactor

---

## Definition of Done

- `app.py` < 200 lines
- Routes separated into modules
- Services handle business logic
- Repositories handle database access only
- Templates organized
- Codebase understandable by another developer