# GardenHub

GardenHub is a local garden-management application built around one idea: **understand the garden first, automate only where it actually helps**.

It started as a Raspberry Pi and Arduino soil-moisture/watering project and has grown into a broader application for planning a garden, organising plant knowledge, using Weather and sensor data, and producing explainable watering recommendations.

GardenHub is still under active development. The current version is a working local prototype, not a finished commercial product or an unattended irrigation controller.

## What works today

GardenHub currently includes:

- a measured 2D **Planner** with persistent layouts;
- plant placement with spacing-aware footprints and quantities;
- beds, structures, surfaces, utilities and visual irrigation objects;
- a read-only **Garden Control** projection based on the saved Planner layout;
- a **Workspace** dashboard combining stored garden, Weather, sensor and Planner information;
- a SQLite-backed **Plant Encyclopedia** with varieties and companion relationships;
- **Open-Meteo** Weather retrieval and stored daily forecast data;
- **ESP32/Arduino soil-moisture ingestion** over HTTP;
- raw-to-percentage moisture calibration;
- explainable **watering recommendations**;
- manual watering records;
- combined **History** for Weather, sensors, watering and system events;
- notification-style presentation of persisted system events;
- a deterministic **demo mode** for development and demonstrations.

The application is designed so the useful parts do not depend on hardware. Planner, Encyclopedia and much of the garden-management experience can be used without sensors or irrigation equipment.

## Important current boundaries

A few distinctions are important when reading the code or trying the application.

### Watering recommendations are not irrigation execution

GardenHub calculates and stores watering recommendations.

It does **not** currently energize valves, relays or pumps. A manual watering action records that watering occurred; it is not a command to hardware and does not verify delivered water.

The scheduler is a **recommendation scheduler**, not a watering controller.

### Planner irrigation is currently visual geometry

The Planner can place and save measured irrigation lines and emitters.

These are not yet a hydraulic network. There is currently no connected pipe topology, flow/pressure calculation, friction-loss model, valve state or automatic shopping calculation.

Those belong to a later irrigation-planning phase.

### Garden Control is read-only

Planner owns editable garden geometry.

Garden Control reads the saved layout and attaches operational information to matching bed objects. It does not edit the layout or silently modify bed/planting records.

### GardenHub is currently single-garden

The application currently operates as one local garden plus a deterministic demo context.

Some frontend garden/location controls anticipate future behaviour, but operational data does not yet have full multi-garden ownership.

## Technology

The current stack is deliberately modest:

- Python
- Flask
- SQLite
- Jinja
- CSS
- vanilla JavaScript
- Open-Meteo
- optional ESP32/Arduino soil-moisture nodes

The backend uses explicit routes, services and repositories rather than an ORM or a larger framework.

That simplicity is intentional. The project should become more complex only when a real product requirement justifies it.

## Architecture at a glance

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
  +--> Planner JSON endpoints

ESP32 / Arduino
  |
  | POST /sensor_data
  v
Sensor receiver
  |
  +--> calibration
  |
  +--> sensor repository
          |
          v
        SQLite

scheduler.py
  |
  +--> Weather refresh
  |
  +--> watering recommendation engine
```

The main SQLite domains are beds/plantings, sensors/readings, plants/varieties/companions, Weather, watering decisions/events, system events and Planner layouts.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the current architecture and domain boundaries.

## Running locally

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Flask application:

```bash
python app.py
```

Run the scheduler separately when Weather/recommendation scheduling is needed:

```bash
python scheduler.py
```

The application is normally available at:

```text
http://localhost:5000
```

For Raspberry Pi/local-network deployment, see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Demo mode

GardenHub includes an isolated deterministic demo database.

Typical commands are:

```bash
python -m gardenhub.seeding.demo reset
python -m gardenhub.seeding.demo seed
python -m gardenhub.seeding.demo serve
```

Demo data is clearly labelled and should never be interpreted as live garden or hardware state.

See [`docs/DEMO_EXPERIENCE.md`](docs/DEMO_EXPERIENCE.md) for the current demo contract.

## Current development status

The present frontend phase is effectively complete for the current version.

The next development phase returns to backend work, beginning with Weather.

Current priority order:

1. finish repository/documentation cleanup and update GitHub;
2. correct Weather freshness, location and data semantics;
3. make Weather scheduling reliable;
4. fix scheduler per-bed/date recommendation behaviour;
5. correct plant mutation and reference-integrity issues;
6. harden sensor ingestion and identity;
7. complete more of the beds/plantings lifecycle;
8. revisit mixed-crop watering logic;
9. improve operational reliability and testing;
10. design the irrigation data model/calculations before building the hydraulic system.

Longer-term work includes the richer Living Garden, Encyclopedia v2, hydraulic irrigation planning, persisted garden location, multi-garden support and eventual safe physical irrigation control.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the maintained roadmap.

## Known issues

The current codebase is intentionally being pushed as a real work-in-progress rather than presented as finished.

Important known backend issues include:

- plant editing can currently lose rich `plant_json` fields;
- sensor ingestion does not yet enforce sensor/bed identity strongly enough;
- the six-reading slot model needs review for multiple sensors in one bed;
- scheduler run guards are process-memory only;
- one bed can currently trigger the scheduler's only recommendation run for the day;
- Weather freshness is based on forecast dates instead of a proper retrieval timestamp;
- Weather timezone/current/history semantics need improvement;
- manual watering validation is still weak;
- mixed-crop watering uses simplified aggregate values;
- variety references need stronger referential protection;
- some frontend status wording is ahead of what the backend can prove;
- there is not yet a general database migration system.

These are tracked development work, not hidden production guarantees.

## Project documentation

The maintained documentation is under `docs/`.

Useful starting points:

- [`PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — what GardenHub currently is
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) — runtime and domain architecture
- [`ROADMAP.md`](docs/ROADMAP.md) — current and future development order
- [`DECISIONS.md`](docs/DECISIONS.md) — architectural decisions worth preserving
- [`DEPLOYMENT.md`](docs/DEPLOYMENT.md) — local/Raspberry Pi deployment
- [`OPERATIONS.md`](docs/OPERATIONS.md) — operating and troubleshooting the current prototype
- [`DEMO_EXPERIENCE.md`](docs/DEMO_EXPERIENCE.md) — deterministic demo mode
- [`BRAND.md`](docs/BRAND.md) — current product identity and assets
- [`GARDENHUB_PLANNER_OBJECTLIBRARY.md`](docs/GARDENHUB_PLANNER_OBJECTLIBRARY.md) — Planner object/asset direction

Older audits, plans and development notes may be kept separately as historical records. They should not be treated as the current source of truth.

## Development and AI assistance

GardenHub is both a real software project and a learning project.

I design the product, define the domain behaviour and architecture, and write the backend as part of learning and improving my Python, Flask, SQLite and general software-development skills.

AI tools are used as development partners, but their role is not the same across the project.

The **backend and domain logic are primarily my own implementation**, developed with ChatGPT used for discussion, explanation, debugging, review and guidance.

The **frontend has received substantially more AI-assisted implementation**. The product behaviour, UX requirements and visual direction are mine, while much of the advanced CSS and parts of the Jinja/HTML and JavaScript — particularly the more complex Planner/frontend work — have been implemented or refined with Codex.

The **documentation represents my project, decisions and development history**. I write and define the underlying content and use ChatGPT to review it, challenge inconsistencies, reorganise outdated material and improve clarity.

I keep this distinction explicit because I want the repository to represent both what I have built and understood myself and where modern AI-assisted development has been part of the implementation process.

## Safety and deployment scope

The current version is intended for local development and trusted local-network use.

It does not currently include:

- public-user authentication;
- authorization;
- CSRF protection;
- hardened device authentication;
- verified irrigation execution;
- controller/valve safety state;
- public-cloud deployment hardening.

Do not expose the current Flask application directly to the public internet or rely on it for unattended physical irrigation.

## Project direction

GardenHub is not intended to become automation for automation's sake.

The aim is to build a garden system that can:

- help someone understand what is growing and where;
- make planning easier;
- combine plant knowledge with the real garden;
- use sensor and Weather data when available;
- explain why it recommends an action;
- eventually design irrigation systems from real measurements;
- later automate only when the system can do so safely and transparently.

The project is still evolving, and the repository reflects that development openly.
