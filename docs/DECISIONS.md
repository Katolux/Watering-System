# GardenHUB Architectural Decisions

This document records decisions that should not be repeatedly reconsidered during the current structural refactor.

---

## ADR-001 — Keep `app.py` as the current Flask constructor

**Status:** Accepted

**Decision**

Keep `app.py` as the Flask constructor and owner of:

- `/`
- `/refresh_weather`
- `/history`

Do not introduce an application factory during the current structural refactor.

**Reason**

`app.py` is already small. Introducing an application factory would add scope and endpoint/import risk without being required for the current organization work.

**Future**

An application factory may be reconsidered after the package structure and tests are stable.

---

## ADR-002 — Structural refactor must preserve behavior

**Status:** Accepted

**Decision**

The v1.3 structural refactor may move and split code but must not change application behavior.

**Preserve**

- algorithms
- SQL
- schemas
- route URLs
- endpoint names
- function signatures
- return values
- templates
- plant JSON
- seeding
- sensor behavior
- weather behavior
- watering behavior
- scheduler behavior
- Arduino behavior

**Reason**

The objective is code organization, not functional redesign.

---

## ADR-003 — Use explicit repository filenames

**Status:** Accepted

**Decision**

Use:

- `beds_repo.py`
- `plants_repo.py`
- `sensors_repo.py`
- `weather_repo.py`
- `watering_repo.py`
- `system_events_repo.py`

**Reason**

Explicit filenames make responsibilities easier to understand and avoid confusion with the top-level `plants/` data folder.

---

## ADR-004 — Keep templates flat during backend restructuring

**Status:** Accepted

**Decision**

Do not move templates into subfolders during the current structural refactor.

**Reason**

Template relocation would change template names and expand the debugging surface without helping the immediate backend organization objective.

**Future**

Template structure may be reconsidered during the visual/product redesign.

---

## ADR-005 — Keep plant seeding manual during development

**Status:** Accepted

**Decision**

Do not seed plants automatically at Flask startup.

Supported command:

```text
python -B seeding/seed_plants.py
```

**Reason**

The development database is intentionally disposable while schemas and data models are changing. Manual seeding keeps the workflow explicit and prevents accidental overwrite behavior.

**Future**

A distributed product may ship with pre-seeded data or a controlled first-run seeding process.

---

## ADR-006 — Keep hardcoded weather coordinates for the current prototype

**Status:** Accepted

**Decision**

Do not replace current hardcoded coordinates during the structural refactor.

**Reason**

The prototype currently serves one garden. User-configurable location is a future product feature, not part of code organization.

**Future**

Location will belong to user/garden configuration and drive weather, frost-date, and seasonal recommendations.

---

## ADR-007 — Distinguish legacy code from experiments

**Status:** Accepted

**Decision**

- confirmed obsolete/broken historical code may move to `dev_tests/legacy/`
- future ML/API experiments may move to `dev_tests/experiments/`
- hardware diagnostics remain in place until separately reviewed
- uncertain helpers remain preserved

**Reason**

Experimental work may have future value and should not be treated as disposable legacy code.

---

## ADR-008 — Plant-data inconsistencies are a separate task

**Status:** Accepted

**Decision**

Do not correct plant filenames, index mismatches, or duplicate/wrong JSON content during the structural refactor.

**Known examples**

- filename mismatches in `plants_index.json`
- `courgette_pation.json` containing duplicated borage data

**Reason**

Data correction and structural movement must remain separate for easier review and rollback.

---

## ADR-009 — Keep product folders at repository root

**Status:** Accepted

**Decision**

Keep these folders at root during the current refactor:

- `plants/`
- `seeding/`
- `templates/`
- `static/`
- `docs/`
- `dev_tests/`

**Reason**

They are clear, conventional, and do not need to move into the Python package for the current application.

---

## ADR-010 — One Codex task per structural objective

**Status:** Accepted

**Decision**

Each Codex task must have one narrow objective and must stop after completing it.

**Task format**

- read permanent project documents
- inspect current repository state
- identify current branch and completed phases
- perform one requested phase
- verify
- report
- stop

**Reason**

Narrow tasks reduce unintended scope, improve reviewability, and align work with small Git commits.
