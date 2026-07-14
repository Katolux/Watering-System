# GardenHUB Codex Guide

## Required Reading

Before beginning any GardenHUB task, read:

1. `docs/PROJECT_OVERVIEW.md`
2. `docs/ARCHITECTURE.md`
3. `docs/REFACTOR_PLAN.md`
4. `docs/DECISIONS.md`

Then inspect the current Git branch and working tree. The repository is the source of truth. Documentation may be updated after structural phases, but current files always take precedence over stale assumptions.

---

## Project Coding Philosophy

GardenHUB is both a real product and a learning project.

The code should look like simple, explicit, professional Python written by a careful early-career developer.

Prefer:

- small modules with clear responsibilities
- plain functions
- direct imports
- understandable control flow
- parameterized SQL
- explicit error handling
- conventional Flask Blueprints
- small, independently testable changes

Avoid introducing complexity merely because it is considered “advanced.”

Do not introduce without explicit approval:

- an ORM
- dependency injection
- async architecture
- microservices
- abstract base classes
- generic repository frameworks
- unnecessary classes
- metaprogramming
- React or another frontend framework
- a full application factory
- large architectural rewrites

---

## Current Structural-Refactor Rule

The current refactor is organizational only.

Allowed work:

- move existing files
- create appropriate package folders
- split oversized files by responsibility
- move existing functions into logical modules
- update imports caused by those moves
- preserve compatibility through temporary re-exports when useful
- move confirmed legacy files into approved legacy folders
- update documentation after a completed phase

Not allowed unless explicitly requested:

- changing algorithms
- changing watering calculations
- changing calibration logic
- changing plant-domain rules
- changing weather behavior
- changing scheduler behavior
- changing SQL
- changing database schema
- changing route URLs
- changing Flask endpoint names
- changing function parameters or return values
- changing template names or render contexts
- changing plant JSON
- changing seeding behavior
- changing Arduino behavior
- changing frontend design
- adding features
- fixing unrelated data inconsistencies

Prefer moving code over rewriting code.

Preserve function bodies wherever practical.

If a structural move appears to require a behavior change, stop and request approval.

---

## Important Current Decisions

- `app.py` remains the Flask constructor and owner of `/`, `/refresh_weather`, and `/history` during this refactor.
- Do not introduce an application factory during the current refactor.
- Templates remain flat.
- Frontend files remain unchanged.
- Plant seeding remains manual during development.
- Supported seeding command:

  ```text
  python -B seeding/seed_plants.py
  ```

- Weather coordinates remain hardcoded during the current version.
- User-configurable location is a future feature.
- Arduino and hardware diagnostic files remain in place until separately reviewed.
- Plant JSON/index inconsistencies are a separate data-correction task.
- Uncertain helpers must be preserved.
- Confirmed legacy code may be quarantined, not silently deleted.
- Experiments must be distinguished from legacy code.

---

## Task Scope Rules

Use one clear objective per Codex task.

At the start of a task, identify:

- project
- current branch
- completed phases
- current task
- files in scope
- files explicitly out of scope
- required verification
- whether committing or pushing is allowed

Do not continue automatically into another phase.

Do not combine:

- structural changes
- functional changes
- frontend/UX changes
- data corrections

Each of those requires a separate task and commit.

---

## Required Working Method

For every structural phase:

1. Inspect the relevant current files.
2. State the exact movement plan.
3. Confirm the files and functions in scope.
4. Make only the requested structural changes.
5. Preserve behavior.
6. Run the required checks.
7. Review `git status`.
8. Confirm original files were removed when moved.
9. Report the result.
10. Stop and wait for approval.

Do not commit or push unless the task explicitly allows it.

---

## Required Verification

Use the checks relevant to the requested phase.

### General

```text
git diff --check
git status --short --branch
python -m compileall app.py scheduler.py gardenhub seeding
```

### Imports

Search for obsolete imports from old module locations.

### Flask

- start the app
- list routes
- compare route URLs, methods, Blueprint names, and endpoint names
- verify key pages

Current key GET routes:

- `/`
- `/history`
- `/automation`
- `/automation/beds`
- `/automation/plants`
- `/automation/sensors`
- `/watering`

### Database

- confirm the same database path is used
- confirm initialization remains idempotent
- preserve table names, columns, constraints, initialization order, and SQL
- use a disposable/development database for write-path checks

### Seeding

- preserve manual seeding
- confirm `python -B seeding/seed_plants.py` still works
- do not add automatic startup seeding

### Sensor receiver

Preserve:

- request fields
- status codes
- raw-to-percentage conversion
- out-of-soil behavior
- slot logic
- insertion behavior

### Watering

Preserve:

- decision factors
- skip conditions
- weather fallback
- persistence tuple shapes
- `/water_now` logging-only behavior

### Scheduler

Preserve:

- morning window
- fallback time
- sleep durations
- in-memory daily run tracking
- weather refresh behavior

---

## Required Completion Report

At the end of every task, report:

1. files moved, created, deleted, or modified
2. functions moved
3. imports updated
4. verification commands and results
5. route-map result
6. database or tuple-shape checks
7. concise diff summary
8. unexpected findings
9. `git status` summary
10. whether a commit was created
11. whether the branch is ahead of remote

Then stop and wait for approval.
